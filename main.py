import os
import sys
import yaml
import logging
from pathlib import Path
from gui import start_gui

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_base_dir():
    """Gets the base directory of the application, whether it's frozen or a script."""
    return Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

def apply_global_env(config):
    """Applies global environment settings from the config."""
    global_env = config.get("global_env", {})
    if not global_env:
        logging.info("No global_env settings found. Skipping.")
        return

    for key, val in global_env.items():
        if key == "PATH_PREPEND":
            if isinstance(val, list):
                prepend_paths = ":".join(str(p) for p in val)
                os.environ["PATH"] = f"{prepend_paths}:{os.environ.get('PATH', '')}"
                logging.info(f"Prepended to PATH: {prepend_paths}")
        else:
            os.environ[key] = str(val)
            logging.info(f"Applied global environment setting: {key}={val}")

def load_config(config_path=None):
    """
    Loads the YAML configuration file.
    If config_path is provided, it uses that.
    Otherwise, it defaults to 'config/config.yaml' relative to the script.
    """
    if config_path:
        path = Path(config_path)
    else:
        path = get_base_dir() / "config" / "config.yaml"

    if not path.exists():
        logging.error(f"Configuration file not found at {path}")
        return None

    logging.info(f"Loading configuration from: {path}")
    with open(path, 'r') as file:
        return yaml.safe_load(file)

def main():
    """
    Main function to load configuration and launch the GUI.
    """
    config = load_config()
    if not config:
        sys.exit(1)

    apply_global_env(config)

    applications = config.get("applications", [])
    if not applications:
        logging.warning("No applications defined in the configuration. The application list will be empty.")

    # Start the GUI
    start_gui(applications)

if __name__ == "__main__":
    main()
