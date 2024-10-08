from setuptools import setup, find_packages

setup(
    name="apache-projects-visualizer",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask",
        "flask-cors",
        "requests",
        "openai",
    ],
    entry_points={
        "console_scripts": [
            "run-visualizer=src.app:main",
        ],
    },
)
