#!/bin/bash

# ==============================================================================
# BuildPilotGUI macOS Application Builder
#
# This script uses PyInstaller to package the Python application into a
# standalone, distributable macOS application bundle (.app).
#
# The final application will be located in the `dist` directory.
# ==============================================================================

echo "--- Building BuildPilotGUI.app ---"

# Ensure the script is running from the directory where it is located
cd "$(dirname "$0")"

# --- 1. Activate Virtual Environment ---
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo >&2 "❌ Error: Virtual environment not found. Please run 'run_macos.sh' first to create it and install dependencies."
    exit 1
fi
echo "1. Activating Python virtual environment..."
source "$VENV_DIR/bin/activate"
echo ""

# --- 2. Run PyInstaller ---
echo "2. Packaging the application with PyInstaller..."
echo "This may take a few moments."

pyinstaller --name="BuildPilotGUI" 
            --windowed 
            --icon="assets/icon.svg" 
            --add-data="config:config" 
            main.py

EXIT_CODE=$?

# Deactivate venv
deactivate

if [ $EXIT_CODE -ne 0 ]; then
    echo >&2 "❌ Error: PyInstaller failed to build the application."
    exit 1
fi
echo ""

# --- 3. Finalizing ---
echo "✅ Success!"
echo "The application has been created at: dist/BuildPilotGUI.app"
echo "You can now run the app directly or drag it to your Applications folder."
echo ""
