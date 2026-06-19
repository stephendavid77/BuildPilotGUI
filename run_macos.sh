#!/bin/bash

# ==============================================================================
# BuildPilotGUI macOS Installer & Launcher
#
# This script automates the setup and execution of the BuildPilotGUI application.
# It performs the following steps:
#   1. Checks if Python 3 is installed.
#   2. Creates a dedicated Python virtual environment (.venv) if it doesn't exist.
#   3. Installs all required dependencies from requirements.txt into the venv.
#   4. Launches the main GUI application using the venv's Python interpreter.
# ==============================================================================

echo "--- BuildPilotGUI Launcher ---"
echo ""

# Ensure the script is running from the directory where it is located
cd "$(dirname "$0")"

# --- 1. Check for Python 3 ---
echo "1. Checking for Python 3..."
if ! command -v python3 &> /dev/null; then
    echo >&2 "❌ Error: Python 3 is not installed on this system."
    echo >&2 'Please install Python 3 to proceed. We recommend using Homebrew: /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew install python'
    exit 1
fi
echo "✅ Python 3 is available."
echo ""

# --- 2. Set up and check the Python Virtual Environment ---
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "2. Creating Python virtual environment in '$VENV_DIR' directory..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo >&2 "❌ Error: Failed to create the Python virtual environment."
        echo >&2 "Please ensure that the 'venv' module is available for your Python 3 installation."
        exit 1
    fi
    echo "✅ Virtual environment created successfully."
    echo ""

    # --- 3. Install Dependencies (only if venv was just created) ---
    echo "3. Installing required application dependencies..."
    # Activate the virtual environment to install packages
    source "$VENV_DIR/bin/activate"
    
    if ! pip install -r requirements.txt; then
        echo >&2 "❌ Error: Failed to install dependencies from requirements.txt."
        # Deactivate before exiting on failure
        deactivate
        exit 1
    fi
    
    # Deactivate after installation is complete
    deactivate
    echo "✅ Dependencies installed successfully."
    echo ""
else
    echo "2. Virtual environment already exists. Skipping creation."
    echo "3. Dependencies are assumed to be installed. Skipping installation."
    echo ""
fi


# --- 4. Launch the BuildPilotGUI Application ---
echo "4. Launching BuildPilotGUI..."
echo "Please wait for the application window to appear."
echo ""

# Activate the virtual environment for running the application
source "$VENV_DIR/bin/activate"

# Execute the main Python script
# The 'exec' command replaces the shell process with the Python process
exec python3 main.py

# The script will end when the Python application closes.
# The 'deactivate' command is not needed here because of 'exec'.
