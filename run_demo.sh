#!/usr/bin/env bash
# Hackathon demo — runs Cosmic SafeCLI with a dangerous command so you see the full flow.
cd "$(dirname "$0")"
# Uses a nonexistent path so nothing in your project can be deleted.
echo "Running demo: python safe.py \"rm -rf /nonexistent/cosmic-demo-safe\""
echo
python3 safe.py "rm -rf /nonexistent/cosmic-demo-safe" 2>/dev/null || python safe.py "rm -rf /nonexistent/cosmic-demo-safe"
