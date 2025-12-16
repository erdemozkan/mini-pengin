from setuptools import setup, find_packages
setup(
    name="mini-pengin",
    version="0.3.0",
    description="Mini PDF pipeline (macOS): DeepSeek-OCR + Docling tables",
    packages=find_packages(),
    entry_points={"console_scripts": ["mini-pengin=mini_pengin.__main__:main"]},
    python_requires=">=3.9",
)
