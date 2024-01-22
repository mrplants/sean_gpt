""" Get the version from a TOML file.
"""
import argparse
import toml

def get_version_from_toml(toml_file):
    """Get the version from the specified TOML file."""
    with open(toml_file, 'r', encoding='utf-8') as file:
        data = toml.load(file)
    return data['tool']['poetry']['version']

def main():
    """ Main function. """
    parser = argparse.ArgumentParser(description='Get the version from a TOML file.')
    parser.add_argument('toml_file', type=str, help='TOML file to get the version from')

    args = parser.parse_args()

    version = get_version_from_toml(args.toml_file)
    print(version)

if __name__ == "__main__":
    main()