"""Minimal LaTeX parser for structured meeting reports."""

from __future__ import annotations

import re
from pathlib import Path

from hybrid_rag.domain.documents import DocumentNode, ParsedDocument
from hybrid_rag.domain.enums import NodeType
from hybrid_rag.parsing.base import BaseParser

_SECTIONING_PATTERN = re.compile(
    r"\\(?P<command>part|chapter|section|subsection|subsubsection|paragraph|subparagraph)\*?\{(?P<title>[^{}]+)\}",
    re.MULTILINE,
)


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
            metadata = {
                "source_file": source.name,
                "sectioning_level": level,
                "title": title,
                "label_value": label_value,
            }
            body = self._clean_text(current_content)
            node = DocumentNode(
                title=title,
                level=level,
                content=body,
                metadata=metadata,
                node_type=NodeType(section_command),
            )
            self._attach_node(document, stack, node)

        return document

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
        text = re.sub(r"\\label\{[^{}]*\}", "", text)
        text = re.sub(r"\\(?:item|noindent)\b", "", text)
        text = re.sub(
            r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}", r"\1", text
        )
        text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", "", text)
        text = text.replace(r"\%", "%")
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()
