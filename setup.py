from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="devscan-pro",
    version="1.0.0",
    author="DevScan Pro Team",
    author_email="support@devscan.pro",
    description="Professional Development Tools Scanner for Ubuntu",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/devscan-pro",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.8+",
    ],
    python_requires=">=3.8",
    install_requires=["requests>=2.28.0"],
    entry_points={
        "console_scripts": ["devscan-pro=devscan_pro:main"],
    },
    include_package_data=True,
)