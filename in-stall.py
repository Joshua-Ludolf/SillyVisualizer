import sys
import javalang
import networkx
import matplotlib

print(f"Python version: {sys.version}")

import pkg_resources

def print_package_version(package_name):
    try:
        version = pkg_resources.get_distribution(package_name).version
        print(f"{package_name} version: {version}")
    except pkg_resources.DistributionNotFound:
        print(f"{package_name} is not installed")

if __name__ == "__main__":
    packages = ["javalang", "networkx", "matplotlib"]
    for package in packages:
        print_package_version(package)