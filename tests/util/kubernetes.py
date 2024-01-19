""" Kubernetes utilities for testing. """
import subprocess
import time
import contextlib
import shutil

def is_command_available(command):
    """Check if a command is available."""
    return shutil.which(command) is not None

@contextlib.contextmanager
def monitor_logs(env):
    """ Monitor the logs of the api deployment. """
    if not is_command_available('stern'):
        print("stern is not installed, skipping log monitoring.")
        yield
    else:
        api_stern_process = subprocess.Popen(
            ['stern', 'api-*', "-n", f"{env}-seangpt", "--since", "1s"])
        try:
            yield
        finally:
            api_stern_process.terminate()

@contextlib.contextmanager
def port_forward(env, port):
    """ Port forward the api deployment. """
    seangpt_port_process = subprocess.Popen([
        "kubectl",
        "port-forward",
        "deployments/api",
        "--namespace",
        f"{env}-seangpt",
        f"{port}:{port}"
    ])
    try:
        # wait for the port-forward to be ready
        time.sleep(2)
        yield
    finally:
        seangpt_port_process.terminate()
