from setuptools import find_packages, setup

setup(
    name="sadar",
    version="0.1.0",
    description="AI-powered RF spectrum anomaly detection system",
    packages=find_packages(include=["src", "src.*"]),
    python_requires=">=3.10,<3.13",
)
