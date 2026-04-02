#!/usr/bin/env bash

resolve_python_bin() {
  if test -n "${PYTHON_BIN:-}"; then
    echo "${PYTHON_BIN}"
    return 0
  fi

  if command -v python3.10 >/dev/null 2>&1; then
    echo "python3.10"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi

  echo "No suitable Python interpreter found." >&2
  return 1
}

setup_venv() {
  local python_bin
  python_bin="$(resolve_python_bin)" || return 1

  if test -d venv; then
    echo "venv exists. Deleting venv."
    rm -rf venv
  fi

  echo "create venv (${python_bin} -m venv venv)"
  "${python_bin}" -m venv venv || return 1

  echo "venv activation (source venv/bin/activate)"
  # This file is meant to be sourced so activation affects the caller shell.
  source venv/bin/activate || return 1

  echo "python -m pip install requirements"
  local requirement_file
  if compgen -G "requirements*.txt" >/dev/null; then
    for requirement_file in requirements*.txt; do
      python -m pip install -r "${requirement_file}" || return 1
    done
  else
    echo "No requirements*.txt files found. Skipping."
  fi

  echo "python -m pip install -e ."
  python -m pip install -e . || return 1
}

run_pytest() {
  python -m pytest \
    -s \
    --log-cli-level=INFO \
    --cov=src/hybrid_rag \
    --cov-report=term-missing \
    --cov-report=html \
    "$@"
}
