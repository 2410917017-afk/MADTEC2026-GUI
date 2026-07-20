from setuptools import setup, find_packages
import os

# Buscar sonyilx-camera si no está disponible en pip/conda
package_data = {}
data_files = []

# Incluir librerías compartidas si existen
site_packages = os.path.join(os.path.dirname(__file__), "src/HMI/hmi/vendor")
if os.path.exists(site_packages):
    package_data["hmi"] = ["vendor/*.so"]

setup(
    name="madtec-hmi",
    version="0.1.0",
    description="HMI application for welding spot process monitoring",
    author="MADTEC",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data=package_data,
    python_requires=">=3.10",
    install_requires=[
        "matplotlib",
        "PyQt5",
        "python-snap7",
        "pyserial",
        "requests",
        "opencv-python-headless",
        "sonyilx-camera",
    ],
    entry_points={
        "console_scripts": [
            "madtec-hmi=HMI.HMI_python:main",
        ],
    },
    include_package_data=True,
)
