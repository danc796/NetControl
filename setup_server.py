from setuptools import setup, find_packages

setup(
    name="mcc_server",
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
            'mcc-server=mcc_server.main:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Multi Computer Controller Server",
    keywords="remote, control, monitoring",
    python_requires=">=3.6",
)