from setuptools import setup, find_packages

setup(
    name="app-launcher",
    version="1.0.0",
    description="A modern PyQt6 application launcher with card mode, compact mode, fuzzy search, favorites, and tray support.",
    author="Jeyaram",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.6",
        "pyinstaller>=6.3"

    ],
    include_package_data=True,
    entry_points={
        "gui_scripts": [
            "app-launcher=main:main"
        ]
    },
)
