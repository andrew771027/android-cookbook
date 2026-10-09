#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." &&
    pwd
)"

FIXTURE_DIR="${PROJECT_ROOT}/fixtures/test-app"

APK_SOURCE="${FIXTURE_DIR}/app/build/outputs/apk/debug/app-debug.apk"

OUTPUT_DIR="${PROJECT_ROOT}/tests/fixtures/test-app"

APK_OUTPUT="${OUTPUT_DIR}/cookbook-test-app.apk"

echo "Building Android Cookbook test APK..."

cd "${FIXTURE_DIR}"

./gradlew assembleDebug

if [[ ! -f "${APK_SOURCE}" ]]; then

    echo "ERROR: APK was not generated:"

    echo "${APK_SOURCE}"

    exit 1

fi

mkdir -p "${OUTPUT_DIR}"

cp "${APK_SOURCE}" "${APK_OUTPUT}"

echo
echo "Test APK ready:"
echo "${APK_OUTPUT}"
