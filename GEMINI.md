# Gemini Agent: BuildPilotGUI Project Context

This document provides a comprehensive overview of the **BuildPilotGUI** project for AI agent assistance. It outlines the project's purpose, architecture, key files, and operational conventions to ensure efficient and accurate collaboration.

## 1. Project Purpose
**BuildPilotGUI** is a professional macOS desktop application built with PySide6 (Qt for Python). It serves as a centralized control panel for managing, configuring, and executing build pipelines for multiple, distinct software projects (e.g., iOS, Android, Spring Boot). Its primary goal is to provide a user-friendly, multi-threaded interface for developers to run complex command sequences without freezing the UI, manage environment variables, and view real-time logs.

## 2. Architecture Overview
The application follows a simple but effective architecture:
- **`main.py`**: The application's main entry point. It is extremely lightweight and its sole responsibility is to invoke the GUI.
- **`gui.py`**: This is the core of the application, containing all UI logic, event handling, and business logic.
  - It uses **PySide6** to construct the entire graphical interface.
  - A `Worker` class, running in a separate `QThread`, executes long-running build commands to prevent the UI from freezing.
  - It manages the application's state, including the loaded configuration and user interactions.
- **`config/config.yaml`**: A single, unified YAML file that stores the entire user configuration. This includes the list of applications, their paths, their specific environment variables, and the multi-step commands associated with them.
- **`~/.config/BuildPilotGUI/settings.json`**: A user-specific settings file stored in the home directory. It currently stores the path to the `config.yaml` file, allowing users to place their configuration anywhere on their system.
- **`run_macos.sh`**: A setup and launcher script that automates the entire installation process, including Python prerequisite checks, virtual environment creation, and dependency installation.

## 3. Key Technologies
- **Language**: Python 3
- **GUI Framework**: PySide6 (The official Qt for Python library)
- **Configuration**: YAML (via `PyYAML` library)
- **Settings**: JSON

## 4. Key Files & Directories
- **`/run_macos.sh`**: **(Primary Entry Point for Users)** The recommended one-click script to install dependencies and launch the application on macOS.
- **`/main.py`**: The technical entry point that starts the GUI application.
- **`/gui.py`**: Contains all application logic, including the `MainWindow`, dialogs for editing configurations, and the multi-threaded `Worker` for executing builds.
- **`/config/config.yaml`**: The master configuration file where all user-defined applications, commands, and environment variables are stored.
- **`/requirements.txt`**: A list of the core Python dependencies (`PyYAML`, `PySide6`).
- **`/.venv/`**: The local Python virtual environment directory created by the `run_macos.sh` script to store dependencies.
- **`~/.config/BuildPilotGUI/settings.json`**: A persistent, user-specific settings file that stores the path to the `config.yaml` file being used.

## 5. Setup & Running the Application
The recommended method for first-time setup and subsequent launches is to use the provided shell script.

1.  **Open a terminal** in the project's root directory.
2.  **Make the script executable** (only needs to be done once):
    ```sh
    chmod +x run_macos.sh
    ```
3.  **Run the script**:
    ```sh
    ./run_macos.sh
    ```
The script will automatically check for Python, create a virtual environment if needed, install dependencies, and launch the application.

## 6. Project Conventions
- **Configuration Management**: All application and build configurations are managed through a single `config.yaml` file. The path to this file is user-configurable via the GUI.
- **UI Responsiveness**: Long-running tasks (build commands) are executed in a separate `QThread` to ensure the GUI remains responsive. The `Worker` class handles this background processing.
- **Error Handling**: User-facing errors (e.g., invalid YAML in the editor, file not found) are communicated through `QMessageBox` dialogs to provide immediate, clear feedback.
- **Styling**: UI styling is done directly in code using Qt Style Sheets (`setStyleSheet`). This is used for coloring buttons and other UI elements to improve user experience.
