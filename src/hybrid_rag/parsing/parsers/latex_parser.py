"""Minimal LaTeX parser for structured meeting reports."""

from __future__ import annotations

import re
from pathlib import Path

from hybrid_rag.domain.documents import (
    BibliographicReference,
    DocumentNode,
    ParsedDocument,
)
from hybrid_rag.domain.enums import NodeType
from hybrid_rag.parsing.base import BaseParser

_SECTIONING_PATTERN = re.compile(
    r"\\(?P<command>part|chapter|section|subsection|subsubsection|paragraph|subparagraph)\*?\{(?P<title>[^{}]+)\}",
    re.MULTILINE,
)
_BIB_RESOURCE_PATTERN = re.compile(r"\\addbibresource\{(?P<path>[^{}]+)\}")


class LatexParser(BaseParser):
    """Parse a limited subset of LaTeX sectioning into a document tree."""

    _LEVELS = {
        "part": 0,
        "chapter": 1,
        "section": 2,
        "subsection": 3,
        "subsubsection": 4,
        "paragraph": 5,
        "subparagraph": 6,
    }

    def can_handle(self, source: Path) -> bool:
        return source.suffix.lower() == ".tex"

    def _load(self, source: Path) -> str:
        return source.read_text(encoding="utf-8")

    def _normalize(self, content: str) -> str:
        stripped_comments = self._strip_comments(content)
        return stripped_comments.replace("\r\n", "\n").replace("\r", "\n")

    def _extract_structure(self, content: str, source: Path) -> ParsedDocument:
        document = ParsedDocument(
            source_path=str(source),
            document_type="latex",
            title=self._infer_document_title(content, source),
        )
        bibliography_paths = self._extract_bibliography_paths(content, source)
        for key, reference in self._load_bibliography_entries(
            bibliography_paths
        ).items():
            document.add_bibliographic_reference(key, reference)
        matches = list(_SECTIONING_PATTERN.finditer(content))

        if not matches:
            fallback_content = self._clean_text(content)
            document.add_root_node(
                DocumentNode(
                    title=document.title or source.stem,
                    level=0,
                    content=fallback_content,
                    node_type=NodeType.DOCUMENT,
                )
            )
            return document

        stack: list[DocumentNode] = []
        for index, match in enumerate(matches):
            section_command = match.group("command")
            title = self._clean_inline_text(match.group("title"))
            level = self._LEVELS[section_command]
            body_start = match.end()
            body_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(content)
            )
            current_content = content[body_start:body_end]
            label_value = re.search(r"\\label\{([^{}]*)\}", current_content)
            label_value = label_value[1] if label_value else ""
            citations = self._extract_citations(current_content)
            body = self._clean_text(current_content)
            metadata = {
                "source_file": source.name,
                "sectioning_level": level,
                "title": title,
                "label_value": label_value,
                "citations": citations,
                "citation_links": self._extract_citation_links(
                    current_content=current_content,
                    cleaned_content=body,
                ),
            }
            node = DocumentNode(
                title=title,
                level=level,
                content=body,
                metadata=metadata,
                node_type=NodeType(section_command),
            )
            for citation_key in citations:
                document.add_bibliographic_reference(
                    citation_key, BibliographicReference()
                )
            self._attach_node(document, stack, node)

        return document

    def _extract_bibliography_paths(self, content: str, source: Path) -> list[str]:
        bibliography_paths: list[str] = []
        for match in _BIB_RESOURCE_PATTERN.finditer(content):
            resolved_path = (source.parent / match.group("path")).resolve()
            path_as_str = str(resolved_path)
            if path_as_str not in bibliography_paths:
                bibliography_paths.append(path_as_str)

        return bibliography_paths

    def _load_bibliography_entries(
        self, bibliography_paths: list[str]
    ) -> dict[str, BibliographicReference]:
        references: dict[str, BibliographicReference] = {}
        for bibliography_path in bibliography_paths:
            path = Path(bibliography_path)
            if not path.exists():
                continue
            references.update(self._parse_bib_file(path))

        return references

    def _parse_bib_file(self, path: Path) -> dict[str, BibliographicReference]:
        content = path.read_text(encoding="utf-8")
        entries: dict[str, BibliographicReference] = {}
        index = 0

        while index < len(content):
            start = content.find("@", index)
            if start == -1:
                break

            brace_start = content.find("{", start)
            if brace_start == -1:
                break

            depth = 1
            cursor = brace_start + 1
            while cursor < len(content) and depth > 0:
                character = content[cursor]
                if character == "{":
                    depth += 1
                elif character == "}":
                    depth -= 1
                cursor += 1

            entry_text = content[start:cursor].strip()
            if entry_text:
                key, reference = self._parse_bibliographic_entry(entry_text, path)
                entries[key] = reference
            index = cursor

        return entries

    def _parse_bibliographic_entry(
        self, entry_text: str, path: Path
    ) -> tuple[str, BibliographicReference]:
        header_match = re.match(
            r"@(?P<entry_type>\w+)\{(?P<key>[^,]+),(?P<body>.*)\}\s*$",
            entry_text,
            re.DOTALL,
        )
        if header_match is None:
            raise ValueError(f"Invalid bibliographic entry in '{path}'.")

        entry_type = header_match.group("entry_type").strip()
        key = header_match.group("key").strip()
        raw_fields = self._parse_bib_fields(header_match.group("body"))
        author_value = raw_fields.get("author", "")
        authors = [
            author.strip()
            for author in author_value.split(" and ")
            if author.strip()
        ]

        return key, BibliographicReference(
            title=raw_fields.get("title"),
            authors=authors,
            year=raw_fields.get("year") or raw_fields.get("date"),
            entry_type=entry_type,
            raw_entry=raw_fields,
        )

    def _parse_bib_fields(self, body: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        for chunk in self._split_bib_fields(body):
            if "=" not in chunk:
                continue
            name, value = chunk.split("=", 1)
            normalized_name = name.strip().lower()
            normalized_value = self._normalize_bib_value(value)
            if normalized_name:
                fields[normalized_name] = normalized_value

        return fields

    def _split_bib_fields(self, body: str) -> list[str]:
        chunks: list[str] = []
        current: list[str] = []
        brace_depth = 0
        in_quotes = False

        for character in body:
            if character == '"' and brace_depth == 0:
                in_quotes = not in_quotes
            elif character == "{":
                brace_depth += 1
            elif character == "}":
                brace_depth = max(0, brace_depth - 1)

            if character == "," and brace_depth == 0 and not in_quotes:
                chunk = "".join(current).strip()
                if chunk:
                    chunks.append(chunk)
                current = []
                continue

            current.append(character)

        tail = "".join(current).strip().rstrip(",")
        if tail:
            chunks.append(tail)

        return chunks

    def _normalize_bib_value(self, value: str) -> str:
        normalized = value.strip().rstrip(",").strip()
        while (
            len(normalized) >= 2
            and ((normalized[0] == "{" and normalized[-1] == "}") or (normalized[0] == '"' and normalized[-1] == '"'))
        ):
            normalized = normalized[1:-1].strip()

        return re.sub(r"\s+", " ", normalized)

    def _post_process(self, document: ParsedDocument) -> None:
        if document.title is None and document.root_nodes:
            document.title = document.root_nodes[0].title

    def _attach_node(
        self,
        document: ParsedDocument,
        stack: list[DocumentNode],
        node: DocumentNode,
    ) -> None:
        while stack and stack[-1].level >= node.level:
            stack.pop()

        if stack:
            stack[-1].add_child(node)
        else:
            document.add_root_node(node)

        stack.append(node)

    def _infer_document_title(self, content: str, source: Path) -> str | None:
        if content is not None and (
            title_match := re.search(r"\\title\{(?P<title>[^{}]+)\}", content)
        ):
            return self._clean_inline_text(title_match["title"])

        return source.stem or None

    def _strip_comments(self, content: str) -> str:
        lines = []
        for line in content.splitlines():
            cleaned_line: list[str] = []
            escape_count = 0
            for character in line:
                if character == "\\":
                    escape_count += 1
                    cleaned_line.append(character)
                    continue
                if character == "%" and escape_count % 2 == 0:
                    break

                escape_count = 0
                cleaned_line.append(character)

            lines.append("".join(cleaned_line))

        return "\n".join(lines)

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\\begin\{itemize\}", "", text)
        text = re.sub(r"\\end\{itemize\}", "", text)
        text = re.sub(r"\\item\b", "- ", text)
        text = self._clean_inline_text(text)
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        return text.strip()

    def _clean_inline_text(self, text: str) -> str:
        text = re.sub(r"\\(textbf|emph)\{([^{}]*)\}", r"\2", text)
        text = re.sub(r"\\footcite\{[^{}]*\}", "", text)
        text = re.sub(r"\\label\{[^{}]*\}", "", text)
        text = re.sub(r"\\(?:item|noindent)\b", "", text)
        text = re.sub(
            r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", text
        )
        text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", "", text)
        text = text.replace(r"\%", "%")
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _extract_citations(self, text: str) -> list[str]:
        citation_matches = re.findall(r"\\footcite\{([^{}]*)\}", text)
        citations: list[str] = []
        for match in citation_matches:
            for raw_key in match.split(","):
                key = raw_key.strip()
                if key and key not in citations:
                    citations.append(key)

        return citations

    def _extract_citation_links(
        self, current_content: str, cleaned_content: str
    ) -> list[dict[str, int | str | list[str]]]:
        citation_links: list[dict[str, int | str | list[str]]] = []
        search_start = 0
        raw_segments = self._extract_citation_segments(current_content)

        for raw_segment in raw_segments:
            citations = self._extract_citations(raw_segment)
            cleaned_sentence = self._clean_text(raw_segment)
            if not citations or not cleaned_sentence:
                continue

            start = cleaned_content.find(cleaned_sentence, search_start)
            if start == -1:
                start = cleaned_content.find(cleaned_sentence)
            if start == -1:
                continue

            end = start + len(cleaned_sentence)
            citation_links.append(
                {
                    "start": start,
                    "end": end,
                    "text": cleaned_sentence,
                    "citations": citations,
                }
            )
            search_start = end

        return citation_links

    def _extract_citation_segments(self, text: str) -> list[str]:
        if item_segments := self._extract_item_segments(text):
            return item_segments

        sentence_pattern = re.compile(
            r"(?P<sentence>.*?\\footcite\{[^{}]*\}.*?(?:[.!?](?=\s|$)|$))",
            re.DOTALL,
        )
        return [
            match.group("sentence").strip()
            for match in sentence_pattern.finditer(text)
            if match.group("sentence").strip()
        ]

    def _extract_item_segments(self, text: str) -> list[str]:
        itemize_pattern = re.compile(
            r"\\begin\{itemize\}(?P<body>.*?)\\end\{itemize\}",
            re.DOTALL,
        )
        item_pattern = re.compile(
            r"\\item\b(?P<item>.*?)(?=\\item\b|$)",
            re.DOTALL,
        )
        segments: list[str] = []

        for block in itemize_pattern.finditer(text):
            body = block.group("body")
            for item_match in item_pattern.finditer(body):
                item_text = item_match.group("item").strip()
                if item_text and "\\footcite{" in item_text:
                    segments.append(item_text)

        return segments
