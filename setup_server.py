from setuptools import setup, find_packages

setup(
    name="nc_server",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "cryptography",
        "psutil",
        "numpy",
        "opencv-python",
        "Pillow",
        "pyautogui",
        "mouse"
    ],
    entry_points={
        'console_scripts': [
            'nc-server=nc_server.main:main',
        ],
    },
)
