#!/usr/bin/env bash
# One-click start script for Digital Twin Embodied Carbon Monitoring Application
set -e

PORT=${PORT:-8000}
HOST=${HOST:-"0.0.0.0"}

echo "=========================================================================="
echo "  DIGITAL TWIN: EMBODIED CARBON MONITORING SYSTEM (CONCRETE CONSTRUCTION)"
echo "  BTP Prototype - EN 15978 / ISO 21930 Standards Compliant"
echo "=========================================================================="
echo "Starting web server on http://localhost:${PORT} ..."
echo "Open your browser to: http://localhost:${PORT}"
echo "Press Ctrl+C to stop."
echo ""

export PYTHONPATH=.
python3 -m uvicorn app:app --host "${HOST}" --port "${PORT}" --reload
