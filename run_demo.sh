#!/usr/bin/env bash
# Hackathon demo — runs Cosmic SafeCLI with a dangerous command so you see the full flow.
cd "$(dirname "$0")"
echo "Running demo: python safe.py \"rm -rf project\""
echo
python3 safe.py "rm -rf project" 2>/dev/null || python safe.py "rm -rf project"
