import sys
import os
import subprocess
import signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QTextEdit, QSplitter, QMessageBox,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QFileDialog,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QFont, QFontMetrics, QIcon
import logging
import yaml
import json
import signal
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Application-wide Constants ---
APP_NAME = "BuildPilotGUI"
SETTINGS_DIR = Path.home() / ".config" / APP_NAME
SETTINGS_PATH = SETTINGS_DIR / "settings.json"
DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "config.yaml"
# ---

def load_app_settings():
    """Loads application settings from a JSON file."""
    if not SETTINGS_PATH.exists():
        return {}
    try:
        with open(SETTINGS_PATH, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load settings from {SETTINGS_PATH}: {e}")
        return {}

def save_app_settings(settings):
    """Saves application settings to a JSON file."""
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(settings, f, indent=4)
        logging.info(f"Settings saved to {SETTINGS_PATH}")
    except IOError as e:
        logging.error(f"Failed to save settings to {SETTINGS_PATH}: {e}")

class AddApplicationDialog(QDialog):
    def __init__(self, parent=None, app_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Application")
        self.layout = QFormLayout(self)
        self.name_input = QLineEdit()
        self.path_input = QLineEdit()
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_path)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_button)
        
        self.layout.addRow("Application Name:", self.name_input)
        self.layout.addRow("Path:", path_layout)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)
        
        if app_data:
            self.name_input.setText(app_data.get("name", ""))
            self.path_input.setText(app_data.get("path", ""))

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Application Directory")
        if directory:
            self.path_input.setText(directory)

    def get_data(self):
        return {"name": self.name_input.text().strip(), "path": self.path_input.text().strip(), "env": {}, "commands": []}


class CommandDialog(QDialog):
    def __init__(self, parent=None, command_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Command")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.layout = QFormLayout(self)
        
        self.name_input = QLineEdit()
        self.steps_input = QTextEdit()
        self.steps_input.setPlaceholderText("Enter command steps, one per line\nExample:\ngit fetch\nmvn clean install")

        self.layout.addRow("Command Name:", self.name_input)
        self.layout.addRow("Steps:", self.steps_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        if command_data:
            self.name_input.setText(command_data.get("name", ""))
            steps = "\n".join(command_data.get("steps", []))
            self.steps_input.setPlainText(steps)

    def get_data(self):
        steps_text = self.steps_input.toPlainText().strip()
        steps = [line.strip() for line in steps_text.split("\n") if line.strip()]
        return {
            "name": self.name_input.text().strip(),
            "steps": steps
        }


class EnvTableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Table setup
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Variable Name (Key)", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Variable")
        self.delete_btn = QPushButton("Delete Selected")
        self.add_btn.clicked.connect(self.add_row)
        self.delete_btn.clicked.connect(self.delete_row)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.delete_btn)
        self.layout.addLayout(button_layout)

    def set_env(self, env_dict):
        self.table.setRowCount(0)
        if not env_dict:
            return
        
        self.table.setRowCount(len(env_dict))
        for row, (key, value) in enumerate(env_dict.items()):
            key_item = QTableWidgetItem(str(key))
            value_item = QTableWidgetItem(str(value))
            self.table.setItem(row, 0, key_item)
            self.table.setItem(row, 1, value_item)

    def get_env(self):
        env_dict = {}
        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            value_item = self.table.item(row, 1)
            
            key = key_item.text().strip() if key_item else ""
            value = value_item.text().strip() if value_item else ""
            
            if key:
                env_dict[key] = value
        return env_dict

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.setCurrentCell(row, 0)

    def delete_row(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return
        
        rows_to_delete = sorted(list(set(
            row for r in selected_ranges for row in range(r.topRow(), r.bottomRow() + 1)
        )), reverse=True)

        for row in rows_to_delete:
            self.table.removeRow(row)


class GlobalEnvDialog(QDialog):
    def __init__(self, parent=None, global_env=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Global Environment Variables")
        self.setMinimumSize(600, 450)
        
        self.layout = QVBoxLayout(self)
        
        self.info_label = QLabel(
            "These global variables are applied to ALL projects and commands executed.\n"
            "Application-specific variables will override these if they have the same name."
        )
        self.info_label.setStyleSheet("color: #666; font-size: 11px;")
        self.layout.addWidget(self.info_label)

        self.env_widget = EnvTableWidget()
        
        self.edit_env = global_env.copy() if global_env else {}
        if "PATH_PREPEND" in self.edit_env and isinstance(self.edit_env["PATH_PREPEND"], list):
            self.edit_env["PATH_PREPEND"] = ":".join(self.edit_env["PATH_PREPEND"])

        self.env_widget.set_env(self.edit_env)
        self.layout.addWidget(self.env_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_data(self):
        raw_env = self.env_widget.get_env()
        if "PATH_PREPEND" in raw_env and raw_env["PATH_PREPEND"]:
            raw_env["PATH_PREPEND"] = [p.strip() for p in raw_env["PATH_PREPEND"].split(":") if p.strip()]
        return raw_env


class Worker(QObject):
    finished = Signal()
    output = Signal(str)

    def __init__(self, application, command_name, global_env=None):
        super().__init__()
        self.application = application
        self.command_name = command_name
        self.global_env = global_env or {}
        self.process = None
        self._is_running = False

    def run(self):
        self._is_running = True
        app_name = self.application.get("name", "Unnamed Application")
        app_path = Path(self.application.get("path", "."))
        app_env = self.application.get("env", {})

        command_to_run = next((cmd for cmd in self.application.get("commands", []) if cmd.get("name") == self.command_name), None)

        if not command_to_run:
            self.output.emit(f"Command '{self.command_name}' not found for '{app_name}'.")
            self.finished.emit()
            return

        original_env = os.environ.copy()
        
        # Apply Global Environment first
        if self.global_env:
            for k, v in self.global_env.items():
                if k == "PATH_PREPEND" and isinstance(v, list):
                    prepend_paths = ":".join(str(p) for p in v)
                    os.environ["PATH"] = f"{prepend_paths}:{os.environ.get('PATH', '')}"
                else:
                    os.environ[k] = str(v)

        # Apply Application Environment second (overriding global if overlap)
        if app_env:
            os.environ.update({k: str(v) for k, v in app_env.items()})

        for step in command_to_run.get("steps", []):
            if not self._is_running:
                break
            
            self.output.emit(f"$ {step}\n")
            try:
                self.process = subprocess.Popen(
                    step, shell=True, cwd=app_path, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, bufsize=1,
                    preexec_fn=os.setsid  # Create a new process group
                )
                for line in iter(self.process.stdout.readline, ''):
                    if not self._is_running:
                        break
                    self.output.emit(line)
                
                self.process.stdout.close()
                return_code = self.process.wait()

                if return_code != 0 and self._is_running:
                    self.output.emit(f"\n--- Step failed with exit code: {return_code} ---\n")
                    break

            except Exception as e:
                self.output.emit(f"Error executing step: {step}\n{e}\n")
                break
        
        os.environ.clear()
        os.environ.update(original_env)
        self.finished.emit()

    def stop(self):
        self.output.emit("\n--- Execution stopped by user. ---\n")
        self._is_running = False
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass


class AllCommandsWorker(QObject):
    finished = Signal()
    output = Signal(str)

    def __init__(self, applications, global_env=None):
        super().__init__()
        self.applications = applications
        self.global_env = global_env or {}
        self.process = None
        self._is_running = False

    def run(self):
        self._is_running = True
        results = []

        for app in self.applications:
            if not self._is_running:
                break
            
            app_name = app.get("name", "Unnamed Application")
            app_path = Path(app.get("path", "."))
            app_env = app.get("env", {})

            for command in app.get("commands", []):
                if not self._is_running:
                    break

                command_name = command.get("name", "Unnamed Command")
                self.output.emit(f"\n{'='*60}\n")
                self.output.emit(f"🚀 Running '{command_name}' for Application '{app_name}'...")
                self.output.emit(f"{'='*60}\n")

                original_env = os.environ.copy()
                
                # Apply Global & App environments
                if self.global_env:
                    os.environ.update({k: str(v) for k, v in self.global_env.items() if k != "PATH_PREPEND"})
                    if "PATH_PREPEND" in self.global_env and isinstance(self.global_env["PATH_PREPEND"], list):
                        prepend = ":".join(str(p) for p in self.global_env["PATH_PREPEND"])
                        os.environ["PATH"] = f"{prepend}:{original_env.get('PATH', '')}"

                if app_env:
                    os.environ.update({k: str(v) for k, v in app_env.items()})

                success = True
                for step in command.get("steps", []):
                    if not self._is_running:
                        success = False
                        break
                    
                    self.output.emit(f"$ {step}\n")
                    try:
                        self.process = subprocess.Popen(
                            step, shell=True, cwd=app_path, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1,
                            preexec_fn=os.setsid
                        )
                        for line in iter(self.process.stdout.readline, ''):
                            if not self._is_running:
                                break
                            self.output.emit(line)
                        
                        self.process.stdout.close()
                        return_code = self.process.wait()

                        if return_code != 0:
                            self.output.emit(f"\n--- Step failed with exit code: {return_code} ---\n")
                            success = False
                            break
                    except Exception as e:
                        self.output.emit(f"Error executing step: {step}\n{e}\n")
                        success = False
                        break
                
                results.append({"app": app_name, "command": command_name, "success": success})
                os.environ.clear()
                os.environ.update(original_env)

        # Generate final report
        report = f"\n\n{'='*30}\n✨ EXECUTION SUMMARY ✨\n{'='*30}\n\n"
        for res in results:
            status_icon = "✅" if res["success"] else "❌"
            report += f"{status_icon} App: {res['app']:<25} | Command: {res['command']:<25} | Status: {'Success' if res['success'] else 'Failure'}\n"
        self.output.emit(report)
        
        self.finished.emit()

    def stop(self):
        self.output.emit("\n--- Execution stopped by user. ---\n")
        self._is_running = False
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass


class QuickStartTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        tutorial_text = """
        <h2 style="color: #007bff; margin-bottom: 5px; font-family: -apple-system, sans-serif;">🚀 Welcome to BuildPilotGUI!</h2>
        <p style="font-family: -apple-system, sans-serif; font-size: 13px; line-height: 1.5; color: #555; margin-bottom: 15px;">
            BuildPilotGUI is your central command dashboard. Instead of keeping multiple terminal windows open for different software projects (e.g., iOS, Android, Spring Boot services), you can configure them once here and execute their build, deployment, or test pipelines with a single click.
        </p>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin-bottom: 15px;" />

        <h3 style="color: #333; margin-top: 0; margin-bottom: 8px; font-family: -apple-system, sans-serif; font-size: 14px;">🛠️ Method 1: Configuring with the Graphical UI (Easiest)</h3>
        <p style="font-family: -apple-system, sans-serif; font-size: 13px; color: #333; line-height: 1.5;">
            You can set up your workspace completely visually inside this application:
        </p>
        <ol style="margin-left: 20px; line-height: 1.7; font-family: -apple-system, sans-serif; font-size: 13px; color: #333; margin-bottom: 15px;">
            <li><b>Add your Project</b>: Click <b>Add</b> under the left panel. Enter a name (e.g. <i>My Service</i>) and browse to the repository folder on your Mac.</li>
            <li><b>Add custom Commands</b>: Select your project on the left. In the <b>Commands</b> tab, click <b>Add Command</b>. Name it (e.g. <i>Build & Run</i>) and write your sequential terminal scripts <b>one command per line</b> (e.g., <code>git pull</code>, then <code>npm install</code> on the next line).</li>
            <li><b>Manage Environment Variables</b>: Go to the <b>Application Env</b> tab, click <b>Add Variable</b> to specify settings specific to this project, and click <b>Save Application Env</b>.</li>
        </ol>

        <h3 style="color: #333; margin-top: 20px; margin-bottom: 8px; font-family: -apple-system, sans-serif; font-size: 14px;">📝 Method 2: Under-the-Hood YAML Configuration (For Power Users)</h3>
        <p style="font-family: -apple-system, sans-serif; font-size: 13px; color: #333; line-height: 1.5;">
            All of your applications, command scripts, and environment overrides are saved in a single configuration file shown in the <b>Config Path</b> at the top. You can edit this file visually by clicking the <b>Edit Config</b> button at the top right. Here is how the structure is formatted:
        </p>
        
        <pre style="background-color: #f8f9fa; border: 1px solid #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 11px; line-height: 1.4; color: #333;">
<b>applications:</b>                 <span style="color: #6a737d;"># A list of all software projects you want to manage</span>
  - <b>name:</b> "iOS App"           <span style="color: #6a737d;"># The friendly display name shown in the left panel</span>
    <b>path:</b> "/Users/path/app"   <span style="color: #6a737d;"># The absolute directory of the project on your Mac</span>
    <b>env:</b>                      <span style="color: #6a737d;"># Project-specific environment variable overrides</span>
      <b>PORT:</b> "3000"
    <b>commands:</b>                 <span style="color: #6a737d;"># List of executable pipelines for this project</span>
      - <b>name:</b> "Install & Run" <span style="color: #6a737d;"># Name shown under the Commands list</span>
        <b>steps:</b>                <span style="color: #6a737d;"># List of terminal commands executed sequentially</span>
          - "git fetch"
          - "pod install"
          - "fastlane build"

<b>global_env:</b>                   <span style="color: #6a737d;"># Environment variables applied to ALL projects and builds</span>
  <b>JAVA_HOME:</b> "/opt/java"
  <b>PATH_PREPEND:</b>               <span style="color: #6a737d;"># Special key to prepend tool directories to your system PATH</span>
    - "/opt/apache-maven/bin"
        </pre>

        <p style="font-family: -apple-system, sans-serif; font-size: 13px; color: #333; line-height: 1.5; margin-top: 15px;">
            💡 <i>Note: When using the <b>Edit Config</b> button, BuildPilotGUI automatically validates your YAML syntax when saving to protect you from configuration corruption.</i>
        </p>

        <h3 style="color: #333; margin-top: 20px; margin-bottom: 8px; font-family: -apple-system, sans-serif; font-size: 14px;">🏃‍♂️ Basic Workflow:</h3>
        <ol style="margin-left: 20px; line-height: 1.7; font-family: -apple-system, sans-serif; font-size: 13px; color: #333;">
            <li><b>Select a Project</b>: Click any application in the left panel.</li>
            <li><b>Select a Command</b>: Pick a command under the <b>Commands</b> tab.</li>
            <li><b>Run & Watch</b>: Click the green <span style="color: #28a745; font-weight: bold;">Run Command</span> button. Logs will stream in real-time below!</li>
        </ol>
        
        <h3 style="color: #333; margin-top: 20px; margin-bottom: 8px; font-family: -apple-system, sans-serif; font-size: 14px;">💡 Pro Tips:</h3>
        <ul style="margin-left: 20px; line-height: 1.7; font-family: -apple-system, sans-serif; font-size: 13px; color: #333; list-style-type: square; margin-bottom: 20px;">
            <li><b>Stop Run</b>: Press the red <span style="color: #dc3545; font-weight: bold;">Stop</span> button to instantly cancel any running commands.</li>
            <li><b>Execute All</b>: Click the blue <span style="color: #007bff; font-weight: bold;">Execute All</span> button at the top to run all pipelines sequentially and view a full success/failure report.</li>
            <li><b>Global Variables</b>: Manage variables globally (via the <span style="font-weight: bold;">Global Env</span> button next to Edit Config).</li>
        </ul>
        """
        
        viewer = QTextEdit()
        viewer.setHtml(tutorial_text)
        viewer.setReadOnly(True)
        viewer.setFrameStyle(0) # Borderless
        layout.addWidget(viewer)


class ConfigEditDialog(QDialog):
    def __init__(self, config_path, parent=None):
        super().__init__(parent)
        self.config_path = config_path
        self.setWindowTitle("Edit Configuration File")
        self.setMinimumSize(800, 600)

        self.layout = QVBoxLayout(self)
        self.editor = QTextEdit()
        self.editor.setLineWrapMode(QTextEdit.NoWrap)
        
        # Use a monospace font for better readability
        font = self.editor.font()
        font.setFamily("monospace")
        font.setStyleHint(QFont.Monospace)
        font_metrics = QFontMetrics(font)
        self.editor.setFont(font)
        self.editor.setTabStopDistance(4 * font_metrics.horizontalAdvance(' '))

        self.layout.addWidget(self.editor)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.save_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.load_file()

    def load_file(self):
        try:
            with open(self.config_path, 'r') as f:
                self.editor.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read config file:\n{e}")
            self.editor.setPlainText(f"# Error loading {self.config_path}\n# {e}")

    def save_and_accept(self):
        content = self.editor.toPlainText()
        try:
            # Validate YAML before saving
            yaml.safe_load(content)
            
            with open(self.config_path, 'w') as f:
                f.write(content)
            
            self.accept()
        except yaml.YAMLError as e:
            QMessageBox.critical(self, "Invalid YAML", f"The configuration is not valid YAML and was not saved.\n\nError: {e}")
        except Exception as e:
            QMessageBox.critical(self, "File Error", f"Could not save file to {self.config_path}:\n{e}")

class MainWindow(QMainWindow):
    def __init__(self, applications, config_path):
        super().__init__()
        self.applications = applications
        self.config_path = config_path
        self.setWindowTitle("BuildPilotGUI")
        self.setGeometry(100, 100, 1200, 800)

        # Set app icon
        icon_path = Path(__file__).parent / "assets" / "icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self.current_thread = None
        self.current_worker = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.init_ui()
        self.populate_applications()

    def on_execute_all_clicked(self):
        self.run_button.setEnabled(False)
        self.execute_all_btn.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log_viewer.clear()
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            global_env = config_data.get("global_env", {})
        except Exception:
            global_env = {}

        self.current_thread = QThread()
        self.current_worker = AllCommandsWorker(self.applications, global_env)
        self.current_worker.moveToThread(self.current_thread)
        
        self.current_thread.started.connect(self.current_worker.run)
        self.current_worker.finished.connect(self.current_thread.quit)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        self.current_thread.finished.connect(self.current_thread.deleteLater)
        self.current_worker.output.connect(self.log_viewer.append)
        
        def cleanup():
            self.run_button.setEnabled(True)
            self.execute_all_btn.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.current_thread = None
            self.current_worker = None
        
        self.current_thread.finished.connect(cleanup)
        self.current_thread.start()

    def show_help_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("How to Use BuildPilotGUI")
        dialog.setMinimumSize(800, 700)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QuickStartTab())
        
        # Add a close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()

    def init_ui(self):
        # --- Define all buttons first ---
        self.browse_config_btn = QPushButton("Browse...")
        self.edit_config_btn = QPushButton("Edit Config")
        self.global_env_btn = QPushButton("Global Env")
        self.help_btn = QPushButton("?")
        self.add_app_button = QPushButton("Add App")
        self.edit_app_button = QPushButton("Edit App")
        self.delete_app_button = QPushButton("Delete")
        self.add_cmd_button = QPushButton("Add Command")
        self.edit_cmd_button = QPushButton("Edit Command")
        self.delete_cmd_button = QPushButton("Delete Command")
        self.run_button = QPushButton("Run Command")
        self.stop_button = QPushButton("Stop")
        self.execute_all_btn = QPushButton("Execute All")
        self.export_log_button = QPushButton("Export Log")
        self.save_env_btn = QPushButton("Save Application Env")

        # --- Top Bar ---
        config_bar_layout = QHBoxLayout()
        config_label = QLabel("Config Path:")
        self.config_path_display = QLineEdit(str(self.config_path))
        self.config_path_display.setReadOnly(True)

        self.browse_config_btn.clicked.connect(self.browse_config_path)
        self.edit_config_btn.clicked.connect(self.edit_config_file)
        self.global_env_btn.clicked.connect(self.edit_global_env)
        
        self.help_btn.clicked.connect(self.show_help_dialog)
        self.help_btn.setFixedSize(28, 28)
        self.help_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                border-radius: 14px;
                border: 1px solid #007bff;
                background-color: #f8f9fa;
                color: #007bff;
            }
            QPushButton:hover {
                background-color: #007bff;
                color: white;
            }
        """)

        config_bar_layout.addWidget(config_label)
        config_bar_layout.addWidget(self.config_path_display)
        config_bar_layout.addWidget(self.browse_config_btn)
        config_bar_layout.addWidget(self.edit_config_btn)
        config_bar_layout.addWidget(self.global_env_btn)
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        config_bar_layout.addSpacerItem(spacer)
        config_bar_layout.addWidget(self.help_btn)
        self.layout.addLayout(config_bar_layout)


        main_splitter = QSplitter(Qt.Horizontal)

        # --- Left panel: App list and buttons ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.app_list_widget = QListWidget()
        self.app_list_widget.itemSelectionChanged.connect(self.on_application_selected)
        
        app_button_layout = QHBoxLayout()
        self.add_app_button.clicked.connect(self.add_application)
        self.edit_app_button.clicked.connect(self.edit_application)
        self.delete_app_button.clicked.connect(self.delete_application)
        app_button_layout.addWidget(self.add_app_button)
        app_button_layout.addWidget(self.edit_app_button)
        app_button_layout.addWidget(self.delete_app_button)

        left_layout.addWidget(self.app_list_widget)
        left_layout.addLayout(app_button_layout)
        main_splitter.addWidget(left_panel)

        # --- Right Panel: QTabWidget ---
        self.tab_widget = QTabWidget()
        
        # Tab 1: Commands
        commands_tab = QWidget()
        commands_layout = QVBoxLayout(commands_tab)
        
        self.command_list_widget = QListWidget()
        
        cmd_button_layout = QHBoxLayout()
        self.add_cmd_button.clicked.connect(self.add_command)
        self.edit_cmd_button.clicked.connect(self.edit_command)
        self.delete_cmd_button.clicked.connect(self.delete_command)
        cmd_button_layout.addWidget(self.add_cmd_button)
        cmd_button_layout.addWidget(self.edit_cmd_button)
        cmd_button_layout.addWidget(self.delete_cmd_button)

        run_control_layout = QHBoxLayout()
        self.run_button.clicked.connect(self.on_run_command_clicked)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: 1px solid #218838;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #218838;
                border-color: #1e7e34;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
                border-color: #1c7430;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #cccccc;
                border-color: #6c757d;
            }
        """)

        self.stop_button.clicked.connect(self.stop_execution)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: 1px solid #c82333;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #c82333;
                border-color: #bd2130;
            }
            QPushButton:pressed {
                background-color: #bd2130;
                border-color: #b21f2d;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #cccccc;
                border-color: #6c757d;
            }
        """)
        
        self.execute_all_btn.clicked.connect(self.on_execute_all_clicked)
        self.execute_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: 1px solid #0069d9;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0069d9;
                border-color: #0062cc;
            }
            QPushButton:pressed {
                background-color: #0062cc;
                border-color: #005cbf;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #cccccc;
                border-color: #6c757d;
            }
        """)

        run_control_layout.addWidget(self.run_button)
        run_control_layout.addWidget(self.stop_button)

        commands_layout.addWidget(self.command_list_widget)
        commands_layout.addLayout(cmd_button_layout)
        commands_layout.addLayout(run_control_layout)
        commands_layout.addWidget(self.execute_all_btn)
        
        # Tab 2: Application Env
        self.env_tab = QWidget()
        env_tab_layout = QVBoxLayout(self.env_tab)
        self.app_env_widget = EnvTableWidget()
        self.save_env_btn.clicked.connect(self.save_app_env)
        env_tab_layout.addWidget(self.app_env_widget)
        env_tab_layout.addWidget(self.save_env_btn)

        self.tab_widget.addTab(commands_tab, "Commands")
        self.tab_widget.addTab(self.env_tab, "Application Env")
        main_splitter.addWidget(self.tab_widget)

        # --- Bottom Panel: Logs ---
        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.addWidget(main_splitter)
        
        log_panel = QWidget()
        log_layout = QVBoxLayout(log_panel)
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.export_log_button.clicked.connect(self.export_log)
        log_layout.addWidget(self.log_viewer)
        log_layout.addWidget(self.export_log_button)
        vertical_splitter.addWidget(log_panel)

        main_splitter.setSizes([300, 900])
        vertical_splitter.setSizes([600, 200])
        self.layout.addWidget(vertical_splitter)

    def populate_applications(self):
        self.app_list_widget.clear()
        for app in self.applications:
            self.app_list_widget.addItem(app.get("name", "Unnamed Application"))

    def on_application_selected(self):
        selected_items = self.app_list_widget.selectedItems()
        if not selected_items:
            self.command_list_widget.clear()
            self.app_env_widget.set_env({})
            return
        
        selected_app_name = selected_items[0].text()
        selected_app = next((app for app in self.applications if app.get("name") == selected_app_name), None)
        
        # Populate Command List
        self.command_list_widget.clear()
        if selected_app:
            for command in selected_app.get("commands", []):
                self.command_list_widget.addItem(command.get("name", "Unnamed Command"))
        
        # Populate Env Table
        if selected_app:
            self.app_env_widget.set_env(selected_app.get("env", {}))

    def save_app_env(self):
        """Saves edited env variables in the table to the selected application."""
        selected_items = self.app_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Save Env", "Please select an application first.")
            return

        selected_app_name = selected_items[0].text()
        selected_app = next((app for app in self.applications if app.get("name") == selected_app_name), None)
        if not selected_app:
            return

        new_env = self.app_env_widget.get_env()
        selected_app["env"] = new_env
        self.save_config()
        QMessageBox.information(self, "Save Env", f"Environment variables saved for application '{selected_app_name}'.")

    def reload_all_from_config(self, config_path):
        """Reloads the entire application state from a given config file."""
        self.config_path = config_path
        self.config_path_display.setText(str(self.config_path))
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            self.applications = config.get("applications", [])
            
            # This applies env vars for future processes, but won't affect the current GUI process
            global_env = config.get("global_env", {})
            if global_env:
                for key, val in global_env.items():
                    if key == "PATH_PREPEND" and isinstance(val, list):
                        prepend = ":".join(str(p) for p in val)
                        os.environ["PATH"] = f"{prepend}:{os.environ.get('PATH', '')}"
                    else:
                        os.environ[key] = str(val)

            self.populate_applications()
            self.command_list_widget.clear()
            self.app_env_widget.set_env({})
            
            QMessageBox.information(self, "Success", f"Successfully loaded new configuration from:\n{config_path}")

        except Exception as e:
            QMessageBox.critical(self, "Config Load Error", f"Failed to load or parse the selected config file.\n\n{e}")
            self.applications = []
            self.populate_applications()


    def browse_config_path(self):
        """Opens a file dialog to select a new config.yaml."""
        directory = str(self.config_path.parent)
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Configuration File", directory, "YAML Files (*.yaml *.yml)"
        )
        if file_path:
            new_config_path = Path(file_path)
            # Save to settings
            settings = load_app_settings()
            settings['config_path'] = str(new_config_path)
            save_app_settings(settings)
            
            # Reload application
            self.reload_all_from_config(new_config_path)

    def edit_config_file(self):
        """Opens a dialog to edit the config file in-place."""
        dialog = ConfigEditDialog(self.config_path, self)
        if dialog.exec():
            # If saved, reload everything
            self.reload_all_from_config(self.config_path)

    def edit_global_env(self):
        """Opens dialog to edit global variables."""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not read config file:\n{e}")
            return

        global_env = config_data.get("global_env", {})
        dialog = GlobalEnvDialog(self, global_env)
        if dialog.exec():
            updated_global_env = dialog.get_data()
            config_data["global_env"] = updated_global_env
            try:
                with open(self.config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
                QMessageBox.information(self, "Global Env", "Global environment variables updated successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not write to config:\n{e}")

    def on_run_command_clicked(self):
        selected_app_items = self.app_list_widget.selectedItems()
        selected_cmd_items = self.command_list_widget.selectedItems()
        if not selected_app_items or not selected_cmd_items:
            QMessageBox.warning(self, "Selection Error", "Please select both an application and a command.")
            return

        selected_app_name = selected_app_items[0].text()
        selected_cmd_name = selected_cmd_items[0].text()
        selected_app = next((app for app in self.applications if app.get("name") == selected_app_name), None)

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log_viewer.clear()
        
        # Load global env from config to pass to the worker
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            global_env = config_data.get("global_env", {})
        except Exception:
            global_env = {}

        self.current_thread = QThread()
        self.current_worker = Worker(selected_app, selected_cmd_name, global_env)
        self.current_worker.moveToThread(self.current_thread)
        self.current_thread.started.connect(self.current_worker.run)
        self.current_worker.finished.connect(self.current_thread.quit)
        self.current_worker.finished.connect(self.current_worker.deleteLater)
        self.current_thread.finished.connect(self.current_thread.deleteLater)
        self.current_worker.output.connect(self.log_viewer.append)
        
        def cleanup():
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.current_thread = None
            self.current_worker = None
        
        self.current_thread.finished.connect(cleanup)
        self.current_thread.start()

    def stop_execution(self):
        if self.current_worker:
            self.current_worker.stop()

    def export_log(self):
        content = self.log_viewer.toPlainText()
        if not content:
            QMessageBox.information(self, "Export Log", "Log is empty.")
            return
        
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Log", "", "Text Files (*.txt);;All Files (*)")
        if filePath:
            try:
                with open(filePath, 'w') as f:
                    f.write(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save log file:\n{e}")

    def add_application(self):
        dialog = AddApplicationDialog(self)
        if dialog.exec():
            new_app_data = dialog.get_data()
            if new_app_data['name'] and new_app_data['path']:
                self.applications.append(new_app_data)
                self.save_config()
                self.populate_applications()
            else:
                QMessageBox.warning(self, "Input Error", "Application name and path cannot be empty.")

    def edit_application(self):
        selected_items = self.app_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select an application to edit.")
            return

        selected_app_name = selected_items[0].text()
        selected_app = next((app for app in self.applications if app.get("name") == selected_app_name), None)
        
        if not selected_app:
            return

        dialog = AddApplicationDialog(self, selected_app)
        if dialog.exec():
            updated_data = dialog.get_data()
            if updated_data['name'] and updated_data['path']:
                selected_app['name'] = updated_data['name']
                selected_app['path'] = updated_data['path']
                self.save_config()
                self.populate_applications()
            else:
                QMessageBox.warning(self, "Input Error", "Application name and path cannot be empty.")

    def delete_application(self):
        selected_items = self.app_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select an application to delete.")
            return

        selected_app_name = selected_items[0].text()
        
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{selected_app_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.applications = [app for app in self.applications if app.get("name") != selected_app_name]
            self.save_config()
            self.populate_applications()
            self.command_list_widget.clear()

    def add_command(self):
        selected_app_items = self.app_list_widget.selectedItems()
        if not selected_app_items:
            QMessageBox.warning(self, "Selection Error", "Please select an application first.")
            return

        selected_app_name = selected_app_items[0].text()
        selected_app = next((app for app in self.applications if app.get("name") == selected_app_name), None)
        
        if not selected_app:
            return

        dialog = CommandDialog(self)
        if dialog.exec():
            new_cmd = dialog.get_data()
            if new_cmd["name"] and new_cmd["steps"]:
                if "commands" not in selected_app:
                    selected_app["commands"] = []
                selected_app["commands"].append(new_cmd)
                self.save_config()
                self.on_application_selected()
            else:
                QMessageBox.warning(self, "Input Error", "Command name and steps cannot be empty.")

    def edit_command(self):
        selected_app_items = self.app_list_widget.selectedItems()
        selected_cmd_items = self.command_list_widget.selectedItems()
        if not selected_app_items or not selected_cmd_items:
            QMessageBox.warning(self, "Selection Error", "Please select both an application and a command to edit.")
            return

        selected_app_name = selected_app_items[0].text()
        selected_cmd_name = selected_cmd_items[0].text()
        
        selected_app = next((app for app in self.applications if app.get("name") == selected_app_name), None)
        if not selected_app:
            return

        selected_cmd = next((cmd for cmd in selected_app.get("commands", []) if cmd.get("name") == selected_cmd_name), None)
        if not selected_cmd:
            return

        dialog = CommandDialog(self, selected_cmd)
        if dialog.exec():
            updated_cmd = dialog.get_data()
            if updated_cmd["name"] and updated_cmd["steps"]:
                selected_cmd["name"] = updated_cmd["name"]
                selected_cmd["steps"] = updated_cmd["steps"]
                self.save_config()
                self.on_application_selected()
            else:
                QMessageBox.warning(self, "Input Error", "Command name and steps cannot be empty.")

    def delete_command(self):
        selected_app_items = self.app_list_widget.selectedItems()
        selected_cmd_items = self.command_list_widget.selectedItems()
        if not selected_app_items or not selected_cmd_items:
            QMessageBox.warning(self, "Selection Error", "Please select both an application and a command to delete.")
            return

        selected_app_name = selected_app_items[0].text()
        selected_cmd_name = selected_cmd_items[0].text()
        
        selected_app = next((app for app in self.applications if app.get("name") == selected_app_name), None)
        if not selected_app:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete command '{selected_cmd_name}' from '{selected_app_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            selected_app["commands"] = [cmd for cmd in selected_app.get("commands", []) if cmd.get("name") != selected_cmd_name]
            self.save_config()
            self.on_application_selected()

    def save_config(self):
        try:
            with open(self.config_path, 'r') as f:
                # We read the file again to preserve any other top-level keys like 'global_env'
                config_data = yaml.safe_load(f) or {}
            
            config_data['applications'] = self.applications
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            logging.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            QMessageBox.critical(self, "Error", f"Could not save config to {self.config_path}:\n{e}")

def start_gui():
    """Main entry point to launch the GUI."""
    # Restore default Ctrl+C behavior for the GUI app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setApplicationName("BuildPilotGUI")
    app.setApplicationDisplayName("BuildPilotGUI")

    # macOS-specific code to set the menu bar name
    if sys.platform == "darwin":
        try:
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if info:
                    info['CFBundleName'] = "BuildPilotGUI"
        except ImportError:
            logging.warning("Could not import Foundation framework. App name may not appear correctly in menu bar.")
            pass

    # Load settings to find the config path
    settings = load_app_settings()
    config_path_str = settings.get("config_path", str(DEFAULT_CONFIG_PATH))
    config_path = Path(config_path_str)

    applications = []
    if not config_path.is_file():
        # Prompt user to find or create the config file
        reply = QMessageBox.question(
            None,
            "Configuration Not Found",
            f"The configuration file could not be found at:\n{config_path}\n\n"
            "Would you like to create a new, empty configuration file at this location?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            try:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    yaml.dump({'applications': [], 'global_env': {}}, f)
                applications = []
            except Exception as e:
                QMessageBox.critical(None, "Creation Failed", f"Could not create the file:\n{e}")
                sys.exit(1)
        else:
            # If user says no, start with a blank slate
            applications = []
    else:
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            applications = config.get("applications", [])
            
            # Apply global environment at startup
            global_env = config.get("global_env", {})
            if global_env:
                for key, val in global_env.items():
                    if key == "PATH_PREPEND" and isinstance(val, list):
                        prepend = ":".join(str(p) for p in val)
                        os.environ["PATH"] = f"{prepend}:{os.environ.get('PATH', '')}"
                    else:
                        os.environ[key] = str(val)

        except Exception as e:
            QMessageBox.critical(None, "Config Load Error", f"Failed to load config:\n{e}")
            applications = []

    window = MainWindow(applications, config_path)
    window.show()
    sys.exit(app.exec())
