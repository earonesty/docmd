# docmd
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


# [docmd](#docmd).genmd
Using docmd from python.

Example:

```
    from docmd import DocMd

    d = DocMd()
    mod = d.importlib("module")
    d.module_gen(mod)
```


## GenMd(object)
Generator class for producing md files.


#### .\_\_init\_\_(self, output\_dir=None, source\_url=None, output\_fh=None)
Construct a DocMd object:

Args:
 - output_dir: folder to write files to (optional)
 - source_url: url for making source links
 - output_fh: file handle to use if no output_dir is specified (sys.stdout)

#### .import\_module(name)
Wrapper for importlib, in case we want to support more ways of specifying a module.

#### .module\_gen(self, mod:module) -> None
Generate markdown, given an imported module with docstring comments.

Returns: name of the module generated.


