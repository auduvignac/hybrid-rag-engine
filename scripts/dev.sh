#!/usr/bin/env bash

setup_venv() {
  if test -d venv; then
    echo "venv exists. Deleting venv."
    rm -rf venv
  fi

  echo "create venv (python3.10 -m venv venv)"
  python3.10 -m venv venv || return 1

  echo "venv activation (source venv/bin/activate)"
  # This file is meant to be sourced so activation affects the caller shell.
  source venv/bin/activate || return 1

  echo "python -m pip install requirements"
  local requirement_found=0
  local requirement_file
  for requirement_file in requirements*.txt; do
    if test -f "${requirement_file}"; then
      requirement_found=1
      python -m pip install -r "${requirement_file}" || return 1
    fi
  done

  if test "${requirement_found}" -eq 0; then
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
