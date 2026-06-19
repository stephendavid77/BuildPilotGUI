# Gemini Agent: BuildPilotGUI Project Context

This document provides a comprehensive overview of the **BuildPilotGUI** project for AI agent assistance. It outlines the project's purpose, architecture, key files, and operational conventions to ensure efficient and accurate collaboration.

## 1. Project Purpose
**BuildPilotGUI** is a professional macOS desktop application designed to be a centralized control panel for managing, configuring, and executing build pipelines. It provides a user-friendly, multi-threaded interface for developers to run complex command sequences, manage environment variables, and view real-time logs for multiple distinct software projects (e.g., iOS, Android, Spring Boot).

## 2. Architecture Overview
The application follows a clean, single-file GUI architecture with helper scripts for setup and distribution.
- **`main.py`**: The application's main entry point. It is extremely lightweight and its sole responsibility is to invoke the GUI.
- **`gui.py`**: The core of the application, containing all UI logic (PySide6), event handling, and business logic.
  - It features a `MainWindow` class that constructs the UI and manages state.
  - A `Worker` class executes single, long-running commands in a separate `QThread` to keep the UI responsive.
  - An `AllCommandsWorker` class iterates through all configured pipelines for the "Execute All" feature.
  - Helper dialogs (`AddApplicationDialog`, `CommandDialog`, `ConfigEditDialog`, etc.) provide modal interfaces for editing.
- **`config/config.yaml`**: A single, unified YAML file that stores the entire user configuration for applications, commands, and environment variables.
- **`~/.config/BuildPilotGUI/settings.json`**: A user-specific settings file that persistently stores the path to the user's chosen `config.yaml` file.
- **Launcher & Builder Scripts**:
  - `run_macos.sh`: A setup script that creates a virtual environment, installs all dependencies from `requirements.txt`, and launches the application for development/local use.
  - `build_app.sh`: A distribution script that uses **PyInstaller** to package the entire project into a standalone, distributable `BuildPilotGUI.app` for macOS.

## 3. Key Technologies
- **Language**: Python 3
- **GUI Framework**: PySide6 (The official Qt for Python library)
- **macOS Integration**: `pyobjc-framework-Cocoa` (to correctly set the app name in the menu bar).
- **Packaging**: PyInstaller (to create the `.app` bundle).
- **Configuration**: YAML (via `PyYAML` library).
- **Settings**: JSON.

## 4. Key Files & Directories
- **`/run_macos.sh`**: The recommended script for setting up the local development environment and running the app.
- **`/build_app.sh`**: The script used to create the final, distributable `BuildPilotGUI.app`.
- **`/main.py`**: The technical entry point that starts the GUI application.
- **`/gui.py`**: Contains all application logic, UI element definitions, and worker threads.
- **`/GEMINI.md`**: This file, providing project context for AI agents.
- **`/assets/icon.svg`**: The SVG application icon used for the app bundle and window.
- **`/config/config.yaml`**: The master configuration file for all user-defined applications and commands.
- **`/requirements.txt`**: A list of all Python dependencies for the project.
- **`/.venv/`**: The local Python virtual environment directory created by `run_macos.sh`.
- **`/dist/`**: The output directory created by `build_app.sh` containing the final `BuildPilotGUI.app`.

## 5. Setup & Running the Application

### For Local Development & Testing
Use the `run_macos.sh` script. It handles virtual environment creation, dependency installation, and launching the app.
```sh
./run_macos.sh
```

### For Distribution
To create a standalone `BuildPilotGUI.app` that can be shared:
1. First, ensure dependencies are installed: `./run_macos.sh` (you can close the app after it launches).
2. Then, run the build script: `./build_app.sh`
3. The final application will be in the `dist/` directory.

## 6. Project Conventions
- **UI Layout**: The UI is defined entirely in code within `gui.py`. The `init_ui` method is structured to define all widgets first, then connect signals, and finally arrange them in layouts.
- **UI Responsiveness**: Long-running tasks are executed in a separate `QThread` via `Worker` classes to ensure the GUI remains responsive.
- **Styling**: UI styling is done directly in code using Qt Style Sheets (`setStyleSheet`). This is used for coloring buttons and other UI elements to improve user experience.
- **Clarity**: Buttons and dialog labels are descriptive (e.g., "Add App", "Application Name") to make the UI as intuitive as possible.
