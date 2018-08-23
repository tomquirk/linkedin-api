import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="linkedin_api",
    version="0.0.1",
    author="Tom Quirk",
    author_email="tomquirkacc@gmail.com",
    description="Python wrapper for the Linkedin API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomquirk/linkedin-api",
    license='MIT',
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
