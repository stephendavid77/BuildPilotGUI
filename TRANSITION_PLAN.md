# Transition Plan: BuildPilot macOS GUI Application

This document outlines the agreed-upon plan and next steps for the transition from the command-line application (`BuildPilot`) to a professional macOS GUI application (`BuildPilotGUI`).

## Core Goal
Create an intuitive, professional, and fully extendable macOS desktop application using **PySide6 (Qt for Python)**. The application should act as a self-sufficient command and build runner, allowing users to add/edit/delete applications, commands, and environment variables directly from the UI.

## Key Architectural Decisions
1.  **Unified Configuration:** Consolidate the multiple YAML files in the `config/` directory into a single, simplified `config.yaml` file.
2.  **Flexible Structure:** The new configuration structure will allow defining multiple "applications" and their associated "commands" and environment variables (e.g., `JAVA_HOME`).
3.  **Portable Configuration:** The application must support loading the `config.yaml` file from any user-specified path on the Mac. The GUI will allow browsing for this file and will remember its location.

---

## Approved Phased Plan

### **Phase 1: Core Refactoring (The "Engine")**
*   **Goal:** Re-architect the application's configuration management and execution logic to support the new flexible system.
*   **Steps:**
    1.  Design and implement the new single `config.yaml` structure.
    2.  Refactor `main.py` and backend scripts in `BuildPilotGUI` to use this new configuration structure.
    3.  Support loading the configuration file from a dynamic, user-specified path.
*   **Result:** A more powerful, generic command runner backend.

### **Phase 2: GUI Development**
*   **Goal:** Build the PySide6 user interface on top of the refactored engine.
*   **Design:**
    *   **Main View:** A list of configured applications on the left, with available commands for the selected application in the main area.
    *   **Execution:** A "Run" button to execute commands, with output routed to a live log viewer at the bottom.
*   **Result:** A working macOS GUI application.

### **Phase 3: In-App Configuration Editing**
*   **Goal:** Make the application fully self-sufficient.
*   **Steps:**
    *   Build GUI forms and interfaces to add, edit, and delete applications, commands, and environment variables directly within the desktop app, updating the `config.yaml` file automatically.
*   **Result:** A complete, self-contained desktop utility.

---

## Next Steps for the New Session
When starting the session in `BuildPilotGUI`, the agent should:
1.  Read this `TRANSITION_PLAN.md` file.
2.  Begin **Phase 1** by refactoring the configuration system (creating the new `config.yaml` structure and updating `main.py` to support it).
