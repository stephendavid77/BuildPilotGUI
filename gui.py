import sys
import os
import subprocess
import signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QTextEdit, QSplitter, QMessageBox,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QFileDialog,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
)
from PySide6.QtCore import Qt, QObject, QThread, Signal
import logging
import yaml
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONFIG_PATH = Path(__file__).parent / "config" / "config.yaml"

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
        
        self.layout.addRow("Name:", self.name_input)
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


class MainWindow(QMainWindow):
    def __init__(self, applications):
        super().__init__()
        self.applications = applications
        self.setWindowTitle("BuildPilotGUI")
        self.setGeometry(100, 100, 1200, 800)
        
        self.current_thread = None
        self.current_worker = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.init_ui()
        self.populate_applications()

    def init_ui(self):
        # Top Bar
        config_bar_layout = QHBoxLayout()
        config_label = QTextEdit("Config Path:")
        config_label.setFrameStyle(0)
        config_label.setMaximumHeight(25)
        config_label.setMaximumWidth(80)
        config_label.setReadOnly(True)
        config_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        config_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.config_path_display = QLineEdit(str(CONFIG_PATH))
        self.config_path_display.setReadOnly(True)
        
        self.global_env_btn = QPushButton("Global Env")
        self.global_env_btn.clicked.connect(self.edit_global_env)

        config_bar_layout.addWidget(config_label)
        config_bar_layout.addWidget(self.config_path_display)
        config_bar_layout.addWidget(self.global_env_btn)
        self.layout.addLayout(config_bar_layout)

        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel: App list and buttons
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        self.app_list_widget = QListWidget()
        self.app_list_widget.itemSelectionChanged.connect(self.on_application_selected)
        
        app_button_layout = QHBoxLayout()
        self.add_app_button = QPushButton("Add")
        self.edit_app_button = QPushButton("Edit")
        self.delete_app_button = QPushButton("Delete")
        self.add_app_button.clicked.connect(self.add_application)
        self.edit_app_button.clicked.connect(self.edit_application)
        self.delete_app_button.clicked.connect(self.delete_application)
        app_button_layout.addWidget(self.add_app_button)
        app_button_layout.addWidget(self.edit_app_button)
        app_button_layout.addWidget(self.delete_app_button)

        left_layout.addWidget(self.app_list_widget)
        left_layout.addLayout(app_button_layout)
        main_splitter.addWidget(left_panel)

        # Right Panel: QTabWidget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Commands
        commands_tab = QWidget()
        commands_layout = QVBoxLayout(commands_tab)
        
        self.command_list_widget = QListWidget()
        
        cmd_button_layout = QHBoxLayout()
        self.add_cmd_button = QPushButton("Add Command")
        self.edit_cmd_button = QPushButton("Edit Command")
        self.delete_cmd_button = QPushButton("Delete Command")
        self.add_cmd_button.clicked.connect(self.add_command)
        self.edit_cmd_button.clicked.connect(self.edit_command)
        self.delete_cmd_button.clicked.connect(self.delete_command)
        cmd_button_layout.addWidget(self.add_cmd_button)
        cmd_button_layout.addWidget(self.edit_cmd_button)
        cmd_button_layout.addWidget(self.delete_cmd_button)

        run_control_layout = QHBoxLayout()
        self.run_button = QPushButton("Run Command")
        self.run_button.clicked.connect(self.on_run_command_clicked)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_execution)
        self.stop_button.setEnabled(False)
        run_control_layout.addWidget(self.run_button)
        run_control_layout.addWidget(self.stop_button)

        commands_layout.addWidget(self.command_list_widget)
        commands_layout.addLayout(cmd_button_layout)
        commands_layout.addLayout(run_control_layout)
        
        # Tab 2: Application Env
        self.env_tab = QWidget()
        env_tab_layout = QVBoxLayout(self.env_tab)
        self.app_env_widget = EnvTableWidget()
        self.save_env_btn = QPushButton("Save Application Env")
        self.save_env_btn.clicked.connect(self.save_app_env)
        env_tab_layout.addWidget(self.app_env_widget)
        env_tab_layout.addWidget(self.save_env_btn)

        self.tab_widget.addTab(commands_tab, "Commands")
        self.tab_widget.addTab(self.env_tab, "Application Env")
        main_splitter.addWidget(self.tab_widget)

        # Bottom Panel: Logs
        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.addWidget(main_splitter)
        
        log_panel = QWidget()
        log_layout = QVBoxLayout(log_panel)
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.export_log_button = QPushButton("Export Log")
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

    def edit_global_env(self):
        """Opens dialog to edit global variables."""
        try:
            with open(CONFIG_PATH, 'r') as f:
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
                with open(CONFIG_PATH, 'w') as f:
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
            with open(CONFIG_PATH, 'r') as f:
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
            with open(CONFIG_PATH, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            
            config_data['applications'] = self.applications
            
            with open(CONFIG_PATH, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            logging.info(f"Configuration saved to {CONFIG_PATH}")
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            QMessageBox.critical(self, "Error", f"Could not save config to {CONFIG_PATH}:\n{e}")

def start_gui(applications):
    app = QApplication(sys.argv)
    window = MainWindow(applications)
    window.show()
    sys.exit(app.exec())
