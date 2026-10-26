#!/usr/bin/env bash
set -euo pipefail

# Run from the root of a clean clone of Raspberry-Pi-Radar.
if [[ ! -f README.md || ! -d templates || ! -d static ]]; then
  echo "Run this script from the Raspberry-Pi-Radar repository root." >&2
  exit 1
fi
if grep -q "## Arduino Uno alternative (laptop-hosted radar interface)" README.md; then
  echo "Arduino section already appears in README.md; not appending twice." >&2
  exit 1
fi
mkdir -p arduino
cp "$(dirname "$0")/arduino/arduino_radar.ino" arduino/arduino_radar.ino
cp "$(dirname "$0")/arduino_app.py" arduino_app.py
cp "$(dirname "$0")/requirements-arduino.txt" requirements-arduino.txt
cat "$(dirname "$0")/README_ARDUINO_SECTION.md" >> README.md

echo "Arduino Uno files copied and Arduino requirements appended to README.md."
echo "Review changes, then commit them on branch arduino-uno-support."
