from setuptools import setup, find_packages

setup(
    name="datalens-cli",
    version="0.1.0",
    description="A lightweight terminal JSON/YAML/TOML intelligent data processing engine",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="DataLens CLI Contributors",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(include=["datalens_cli*"]),
    install_requires=[],
    extras_require={
        "yaml": ["pyyaml>=5.3"],
        "toml": ["toml>=0.10"],
        "all": ["pyyaml>=5.3", "toml>=0.10"],
    },
    entry_points={
        "console_scripts": [
            "datalens=datalens_cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Utilities",
    ],
)
