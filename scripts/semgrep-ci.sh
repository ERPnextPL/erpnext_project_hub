#!/usr/bin/env bash
set -euo pipefail

RULES_DIR="frappe-semgrep-rules"

if ! command -v semgrep >/dev/null 2>&1; then
  if [[ "${CI:-}" == "true" ]]; then
    python -m pip install semgrep
  else
    echo "semgrep not found; skipping Semgrep for local pre-commit. Install it with: python -m pip install semgrep" >&2
    exit 0
  fi
fi

if [[ ! -d "${RULES_DIR}" ]]; then
  git clone --depth 1 https://github.com/frappe/semgrep-rules.git "${RULES_DIR}"
fi

semgrep ci --config "./${RULES_DIR}/rules" --config r/python.lang.correctness
