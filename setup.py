from setuptools import setup, find_packages

setup(
    name="pymoodle",
    version="0.0.0",
    description="A Python client for Moodle Web Service API.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Aathish Sivasubrahmanian",
    author_email="aathish04@gmail.com",
    url="https://github.com/Aathish04/pymoodle",  # Add your repo URL
    packages=find_packages(),
    install_requires=[
        "requests",  # External dependencies
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
