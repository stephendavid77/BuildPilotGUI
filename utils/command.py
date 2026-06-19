import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(command, cwd=None, output_callback=None):
    """
    Executes a command and streams its output in real-time via a callback.

    Args:
        command (str): The command to execute.
        cwd (str, optional): The working directory. Defaults to None.
        output_callback (callable, optional): A function to call with each line of output.

    Returns:
        dict: A dictionary containing the process's exit code, and captured stdout and stderr if no callback is provided.
    """
    if output_callback:
        try:
            process = subprocess.Popen(
                command, shell=True, cwd=cwd, stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            for line in iter(process.stdout.readline, ''):
                output_callback(line)
            process.stdout.close()
            return_code = process.wait()
            return {"exit_code": return_code, "stdout": "", "stderr": ""}
        except Exception as e:
            error_msg = f"Error executing command: {command}\n{e}"
            logging.error(error_msg)
            output_callback(error_msg + "\n")
            return {"exit_code": 1, "stdout": "", "stderr": str(e)}
    else:
        try:
            result = subprocess.run(command, shell=True, check=True, cwd=cwd, capture_output=True, text=True)
            return {"exit_code": 0, "stdout": result.stdout.strip(), "stderr": ""}
        except subprocess.CalledProcessError as e:
            return {"exit_code": e.returncode, "stdout": e.stdout.strip(), "stderr": e.stderr.strip()}
