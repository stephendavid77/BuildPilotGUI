# BuildPilotGUI

BuildPilotGUI is a professional, multi-project macOS desktop control panel built with **PySide6 (Qt for Python)**. It acts as an intuitive dashboard that lets you manage, configure, and build multiple distinct projects (e.g., iOS, Android, Spring Boot, Python) from a single user interface.

With a fully responsive, multi-threaded layout, you can trigger custom build pipelines, manage environment variables, and see real-time log outputs without freezing your screen.

---

## Core Features

- 🖥️ **Visual Dashboard**: Clean macOS native look and feel.
- 📁 **Active Config Locator**: Path to your configuration file is displayed at the top for easy reference and copying.
- 🛠️ **In-App Project Management**: Add, edit, and delete different projects (applications) directly inside the GUI.
- ⚙️ **Custom Commands Editor**: Create and edit custom commands and write their sequential shell steps (e.g., `git fetch`, `pod install`, `mvn clean install`) line-by-line.
- 🧵 **Multi-Threaded Live Logging**: Long-running builds execute in background threads. Real-time stdout and stderr output are piped directly to the log window.
- 🛑 **Stop Execution**: Kill running builds/command groups instantly with a dedicated "Stop" button that terminates process groups.
- 📄 **Export Log**: Save any terminal output to a local `.txt` file for debugging or sharing.
- 🌐 **Global & Local Env Editor**: Interactive spreadsheet-like tables to add and manage:
  - **Global Variables** (applies to all projects, like `JAVA_HOME`).
  - **Application Variables** (isolated environment overrides for specific projects).

---

---

## Master Configuration (`config.yaml`)

Your configurations are loaded from and saved to a single file: `config/config.yaml`. 

You can edit this file directly in a text editor, or **modify it completely from inside the desktop GUI**.

### Structure Overview

- `applications`: A list of projects you want to manage.
  - `name`: Display name.
  - `path`: The absolute path to the project's root folder.
  - `env`: Key-value map of environment variables specific to this project.
  - `commands`: List of executable build pipelines.
    - `name`: Command name.
    - `steps`: An ordered list of shell commands to run.
- `global_env`: Key-value environment variables applied globally to all running commands.
  - `PATH_PREPEND`: A special key containing a list of directory paths to prepend to your system `PATH` (ideal for linking correct compiler binaries).

**Example Structure:**
```yaml
applications:
  - name: "My Spring Service"
    path: "/Users/username/projects/my-service"
    env:
      DB_PORT: "5432"
    commands:
      - name: "Build & Install"
        steps:
          - "git fetch"
          - "git checkout master"
          - "mvn clean install -Dmaven.test.skip=true"

global_env:
  JAVA_HOME: "/opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
  PATH_PREPEND:
    - "/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home/bin"
```

---

## How to Use BuildPilotGUI

### 1. Launching the App
Run the following command in your terminal to start the control panel:
```sh
python3 main.py
```

### 2. Managing Applications
- **Add**: Click "Add" under the application panel, enter a name, and click "Browse..." to select your local project's root directory.
- **Edit**: Select an application and click "Edit" to modify its name or directory path.
- **Delete**: Select an application and click "Delete" to remove it from your control panel directory. *(This will never delete your local project files, only the entry in config.yaml).*

### 3. Editing Commands & Steps
- Select an application on the left, then open the **Commands** tab.
- Click **Add Command** to create a pipeline. In the text box, enter steps line-by-line (e.g., step 1: `git checkout master`, step 2: `git pull`).
- Select any command and click **Edit Command** to update steps, or **Delete Command** to remove it.

### 4. Running and Stopping
- Select an application, click on a command, and click **Run Command**.
- The progress terminal at the bottom will stream live command steps and stdout.
- To abort a running pipeline at any point, click the **Stop** button.

### 5. Managing Environment Variables
- **Application Env**: Open the "Application Env" tab on the right side. You can double-click cells to edit existing keys and values, or click "Add Variable" and "Delete Selected". Click **Save Application Env** to persist the changes.
- **Global Env**: Click **Global Env** in the top bar. A window will open showing global settings. Edit your environment tables, then click "Save" to apply and write to the master config.
