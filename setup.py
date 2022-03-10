from setuptools import setup


def long_description():
    from os import path

    this_directory = path.abspath(path.dirname(__file__))
    with open(path.join(this_directory, "README.md")) as readme_f:
        contents = readme_f.read()
        return contents


setup(
    name="docmd",
    version="1.0.5",
    description="Convert python docstring documentation to github markdown files",
    packages=["docmd"],
    url="https://github.com/AtakamaLLC/docmd",
    long_description=long_description(),
    long_description_content_type="text/markdown",
    setup_requires=["wheel"],
    entry_points={
        "console_scripts": ["docmd=docmd.__main__:main"],
    },
)
