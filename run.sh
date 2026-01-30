#!/bin/bash
#
# Simple launcher script for the pen plotter GUI
#
# Usage:
#   ./run.sh     # Launch the interactive GUI

set -e  # Exit on error

echo "======================================================================"
echo "  Pen Plotter Control - Interactive GUI"
echo "======================================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Unset PYTHONPATH to avoid conflicts with system Python packages
unset PYTHONPATH

# Launch the matplotlib-based GUI
python -m penplotter

echo ""
echo "======================================================================"
echo "  GUI closed"
echo "======================================================================"
