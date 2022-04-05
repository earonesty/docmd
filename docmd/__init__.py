"""
Generate api-style github markdown-files from python docstrings.

```
pip install docmd
```

Generate one file:

```
docmd my_module > README.md
```

Generate a whole folder full of documentation:

```
docmd my_module -out docs -url https://github.com/atakamallc/docmd/blob/master
```
"""

from .genmd import GenMd
