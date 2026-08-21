#!/usr/bin/env bash

set -e

echo "=== Android Cookbook Environment Check ==="

echo
echo "[1] Checking adb..."

command -v adb

echo
adb version


echo
echo "[2] Starting adb server..."

adb start-server


echo
echo "[3] Listing devices..."

adb devices -l


echo
echo "[4] Checking emulator..."

if command -v emulator >/dev/null 2>&1; then
    emulator -version
else
    echo "Android emulator command not found"
fi


echo
echo "[5] Environment check complete."
