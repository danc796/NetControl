from setuptools import setup, find_packages

setup(
    name="mcc_client",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "tkinter",
        "customtkinter",
        "cryptography",
        "opencv-python",
        "pillow",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "nc-client=nc_client.main:main",
        ],
    },
)
