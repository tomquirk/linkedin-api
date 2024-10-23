import subprocess
import sys


def lint():
    flake8_result = subprocess.run(["flake8", "."], capture_output=True, text=True)
    black_result = subprocess.run(["black", "--check", "."], capture_output=True, text=True)

    print(flake8_result.stdout)
    print(black_result.stdout)

    if flake8_result.returncode != 0 or black_result.returncode != 0:
        sys.exit(1)


def format():
    result = subprocess.run(["black", "."], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        sys.exit(1)


if __name__ == "__main__":
    globals()[sys.argv[1]]()
