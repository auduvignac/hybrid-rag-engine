#!/usr/bin/env bash

# This file is intended to be sourced, so these options affect the caller shell.
set -euo pipefail

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

install_project_in_venv() {
  if ! test -f venv/bin/activate; then
    echo "Missing venv/bin/activate. Run setup_venv or rebuild_venv first." >&2
    return 1
  fi

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

setup_venv() {
  local python_bin
  python_bin="$(resolve_python_bin)" || return 1

  if test -d venv; then
    echo "venv already exists. Reusing it."
    install_project_in_venv || return 1
    return 0
  fi

  echo "create venv (${python_bin} -m venv venv)"
  "${python_bin}" -m venv venv || return 1

  install_project_in_venv || return 1
}

rebuild_venv() {
  if test -d venv; then
    echo "venv exists. Deleting venv."
    rm -rf venv || return 1
  fi

  setup_venv || return 1
}

run_pytest() {
  local venv_dir="${VENV_DIR:-venv}"
  local python_bin="${venv_dir}/bin/python"

  if ! test -x "${python_bin}"; then
    echo "Error: expected virtualenv Python at '${python_bin}' but it was not found or is not executable." >&2
    echo "Run setup_venv or rebuild_venv first." >&2
    return 1
  fi

  "${python_bin}" -m pytest \
    -s \
    --log-cli-level=INFO \
    --cov=src/hybrid_rag \
    --cov-report=term-missing \
    --cov-report=html \
    "$@"
}
