"""Installation information/metadata."""
import os
import subprocess

import setuptools

soft7_version = (
    subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE, check=True)
    .stdout.decode("utf-8")
    .strip()
)
assert "." in soft7_version

assert os.path.isfile("soft/version.py")
with open("soft/VERSION", "w", encoding="utf-8") as fh:
    fh.write(f"{soft7_version}\n")

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="soft7-pkg-quaat",
    version=soft7_version,
    author="Quaat",
    author_email="nims@quaat.com",
    description="SOFT7 semantic interoperability framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SINTEF/soft7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    package_data={"soft7-pkg-quaat": ["VERSION"]},
    include_package_data=True,
    python_requires=">=3.7",
)
