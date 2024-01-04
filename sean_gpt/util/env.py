from typing import List
import os
import yaml
import logging

def yaml_env(yaml_file_path:str, drill_down_path: List[str]=None, prefix:str = "") -> None:
    """ Loads environment variables from a YAML file.

    This function reads a YAML file and sets environment variables based on the
    drill-down path provided. The environment variable names are created by
    joining the key names with an underscore.

    Parameters:
    yaml_file_path (str): The path to the YAML file.
    drill_down_path (list, optional): A list of keys specifying the path to
        drill down in the YAML structure. For example, ['env', 'jwt']
        corresponds to data['env']['jwt'] in the YAML structure.
    prefix (str, optional): A prefix to prepend to the environment variable

    Returns:
    None
    """
    # if the file does not exist, do nothing
    if not os.path.exists(yaml_file_path):
        logging.info(f"YAML file {yaml_file_path} does not exist.")
        return
    with open(yaml_file_path, 'r') as f:
        logging.info(f"Loading ENV from YAML file {yaml_file_path}.")
        data = yaml.safe_load(f)

    if drill_down_path:
        for path in drill_down_path:
            data = data.get(path, {})
    # raise an error if the drill-down path does not exist
    if not data:
        raise ValueError(f"Drill-down path {drill_down_path} does not exist in YAML file {yaml_file_path}.")

    # This could contain multi-level values, so use DFS and create a new env var
    # for each leaf node
    def dfs(data, drill_prefix):
        if isinstance(data, dict):
            for key, value in data.items():
                dfs(value, drill_prefix + key + '_')
        else:
            env_var_name = prefix + drill_prefix[:-1]
            # Don't override existing env vars
            if env_var_name not in os.environ:
                os.environ[env_var_name] = str(data)
    dfs(data, '')