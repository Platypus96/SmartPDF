#!/bin/bash

# Default to Round 1A if the environment variable is not set
if [ -z "$ROUND_SCRIPT" ]; then
  echo "ROUND_SCRIPT not set. Defaulting to Round 1A."
  exec python src/round_1a.py
elif [ "$ROUND_SCRIPT" = "1a" ]; then
  echo "Running Round 1A..."
  exec python src/round_1a.py
elif [ "$ROUND_SCRIPT" = "1b" ]; then
  echo "Running Round 1B..."
  exec python src/round_1b.py
else
  echo "Error: Unknown value for ROUND_SCRIPT: $ROUND_SCRIPT"
  exit 1
fi