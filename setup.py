import setuptools
import ast
import re
from pathlib import Path

CURRENT_DIR = Path(__file__).parent


def get_long_description() -> str:
    readme_md = CURRENT_DIR / "README.md"
    with open(readme_md, encoding="utf8") as ld_file:
        return ld_file.read()



setuptools.setup(
    name="linkedin_api",
    version="1.1.1.1",
    author="Tom Quirk",
    author_email="tomquirkacc@gmail.com",
    description="Python wrapper for the Linkedin API",
    long_description="sdf",
    long_description_content_type="text/markdown",
    url="https://github.com/tomquirk/linkedin-api",
    license="MIT",
    packages=setuptools.find_packages(),
    install_requires=["requests"],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
