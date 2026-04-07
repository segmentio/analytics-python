#!/bin/bash
#
# Run E2E tests for analytics-python
#
# Prerequisites: Python 3, pip, Node.js 18+
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

echo "=== Building analytics-python e2e-cli ==="

# Install SDK
cd "$SDK_ROOT"
pip install -e .

# Install e2e-cli
cd "$SCRIPT_DIR"
pip install -e .

echo ""

# Run tests
cd "$E2E_DIR"
./scripts/run-tests.sh \
    --sdk-dir "$SCRIPT_DIR" \
    --cli "e2e-cli" \
    "$@"
