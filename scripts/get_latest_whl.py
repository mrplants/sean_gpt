import argparse
import os
from packaging.version import parse

def get_latest_wheel(directory):
    """Find the latest wheel file in the specified directory."""
    wheel_files = [f for f in os.listdir(directory) if f.endswith('.whl')]
    if not wheel_files:
        return "No wheel files found."

    latest_wheel_file = max(wheel_files, key=lambda f: parse(f.split('-')[1]))
    return latest_wheel_file

def main():
    parser = argparse.ArgumentParser(description='Find the latest wheel file in a directory.')
    parser.add_argument('directory', type=str, help='Directory containing wheel files')

    args = parser.parse_args()

    latest_wheel = get_latest_wheel(args.directory)
    print(latest_wheel)

if __name__ == "__main__":
    main()
