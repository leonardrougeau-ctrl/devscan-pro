# Complete setup.py - add the missing parts
from setuptools import setup, find_packages

setup(
    name="devscan-pro",
    version="1.1.0",
    description="Professional Development Tools Scanner",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author="Your Name",  # Change to your actual name
    author_email="your@email.com",  # Change to your actual email
    url="https://github.com/yourusername/devscan-pro",  # Change to your actual GitHub URL
    packages=find_packages(),
    install_requires=[
        'requests>=2.28.0',
    ],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: Other/Proprietary License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Systems Administration',
    ],
    # ADD THESE LINES for proper executable
    entry_points={
        'console_scripts': [
            'devscan-pro=devscan_pro:main',
        ],
    },
    include_package_data=True,  # Include non-Python files
)