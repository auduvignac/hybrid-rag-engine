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

install_project_in_venv() {
  local venv_dir="${VENV_DIR:-venv}"

  if ! test -f "${venv_dir}/bin/activate"; then
    echo "Missing ${venv_dir}/bin/activate. Run setup_venv or rebuild_venv first." >&2
    return 1
  fi

  echo "venv activation (source ${venv_dir}/bin/activate)"
  # This file is meant to be sourced so activation affects the caller shell.
  source "${venv_dir}/bin/activate" || return 1

  echo "python -m pip install requirements"
  local requirement_files=()
  local requirement_file
  if compgen -G "requirements*.txt" >/dev/null; then
    while IFS= read -r requirement_file; do
      requirement_files+=("${requirement_file}")
    done < <(printf '%s\n' requirements*.txt | sort)

    for requirement_file in "${requirement_files[@]}"; do
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
  local venv_dir="${VENV_DIR:-venv}"
  python_bin="$(resolve_python_bin)" || return 1

  if test -d "${venv_dir}"; then
    echo "${venv_dir} already exists. Reusing it."
    install_project_in_venv || return 1
    return 0
  fi

  echo "create venv (${python_bin} -m venv ${venv_dir})"
  "${python_bin}" -m venv "${venv_dir}" || return 1

  install_project_in_venv || return 1
}

rebuild_venv() {
  local venv_dir="${VENV_DIR:-venv}"

  if test -d "${venv_dir}"; then
    echo "${venv_dir} exists. Deleting ${venv_dir}."
    rm -rf "${venv_dir}" || return 1
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
