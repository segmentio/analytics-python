#!/bin/bash
#
# Run E2E tests for analytics-python
#
# Prerequisites: Node.js 18+ and one of:
#   - devbox (recommended): run `devbox shell` first, then ./run-e2e.sh
#   - Python 3.9+ with a virtualenv already activated
#
# Usage:
#   ./run-e2e.sh [extra args passed to run-tests.sh]
#
# Override sdk-e2e-tests location:
#   E2E_TESTS_DIR=../my-e2e-tests ./run-e2e.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_ROOT="$SCRIPT_DIR/.."
E2E_DIR="${E2E_TESTS_DIR:-$SDK_ROOT/../sdk-e2e-tests}"

# Resolve python and pip — prefer activated venv/devbox python, fall back to python3
PYTHON="${PYTHON:-$(command -v python || command -v python3)}"
PIP="$PYTHON -m pip"

if [[ -z "$PYTHON" ]]; then
    echo "Error: Python not found. Run 'devbox shell' first or activate a virtualenv."
    exit 1
fi

echo "=== Building analytics-python e2e-cli ==="
echo "Using Python: $PYTHON"

# Install SDK
cd "$SDK_ROOT"
$PIP install -e . -q

# Install e2e-cli
cd "$SCRIPT_DIR"
$PIP install -e . -q

echo ""

# Run tests
cd "$E2E_DIR"
./scripts/run-tests.sh \
    --sdk-dir "$SCRIPT_DIR" \
    --cli "e2e-cli" \
    "$@"
