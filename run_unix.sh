#!/bin/bash
# ==========================================================
#  Future Envelope — Mac/Linux Setup Script
#  Run once: bash run_unix.sh
# ==========================================================

set -e

echo ""
echo " [1/4] Creating virtual environment (venv)..."
python3 -m venv venv

echo " [2/4] Activating venv and upgrading pip..."
source venv/bin/activate
pip install --upgrade pip --quiet

echo " [3/4] Installing dependencies..."
pip install -r requirements.txt

echo " [4/4] Starting Future Envelope..."
echo "       Open http://127.0.0.1:5000 in your browser."
echo "       Press Ctrl+C to stop."
echo ""
python app.py
