"""
Using docmd from python.

Example:

```
    from docmd import DocMd

    d = DocMd()
    mod = d.importlib("module")
    d.module_gen(mod)
```
"""
import io
import sys
import importlib
import os

import pathlib
import logging as log
from types import ModuleType
from typing import IO, Generic

from docmd.docmod import DocMod, DocCls, DocFunc

log.basicConfig()


def escapemd(txt):
    """Escape underscores."""
    return txt.replace("_", "\\_")


class DocMd:
    """Generator class for producing md files."""

    def __init__(self, output_dir=None, source_url=None, output_fh=None):
        """Construct a DocMd object:

        Args:
         - output_dir: folder to write files to (optional)
         - source_url: url for making source links
         - output_fh: file handle to use if no output_dir is specified (sys.stdout)
        """
        self.source_url = source_url
        self.source_path = None
        if output_dir:
            self.output_fh = None
            self.dir = pathlib.Path(output_dir)
            self.dir.mkdir(exist_ok=True)
            self.module_links = True
        else:
            self.output_fh = output_fh or sys.stdout
            self.dir = None
            self.module_links = False

    @staticmethod
    def __module_name_to_md(module_name):
        return module_name.replace(".", "_") + ".md"

    def __get_output_file(self, module_name):
        if self.dir:
            path = self.dir / self.__module_name_to_md(module_name)
            return path.open("w")
        return self.output_fh

    @staticmethod
    def import_module(name):
        """Wrapper for importlib, in case we want to support more ways of specifying a module."""
        return importlib.import_module(name)

    def __module_header(self, file: IO, docmod: DocMod):
        hash_level = "#" * 1
        name = docmod.name
        text = docmod.doc
        if "." in name:
            # link back to top
            parent_name, child_name = name.rsplit(".", 1)
            if self.module_links:
                parent_link = self.__module_name_to_md(parent_name)
                print(
                    f"{hash_level} [{escapemd(parent_name)}]({parent_link}).{child_name}",
                    file=file,
                )
            else:
                parent_link = "#" + parent_name.replace(".", "_")
                print(
                    f"{hash_level} [{escapemd(parent_name)}]({parent_link}).{child_name}",
                    file=file,
                )
        else:
            # top level module
            print(f"{hash_level} {escapemd(name)}", file=file)

        if text:
            print(text, file=file)
        else:
            log.warning("no docstring for: %s", name)
        print("\n", file=file)

    @staticmethod
    def __get_kids(ent):
        pub = getattr(ent, "__all__", None)
        if not pub:
            pub = []
            for name in ent.__dict__:
                if name.startswith("_") and name != "__init__":
                    continue
                pub.append(name)
        pub = sorted(pub)
        res = []
        for name in pub:
            obj = getattr(ent, name, None)
            if obj is not None:
                res.append((name, obj))

        return res

    @staticmethod
    def _func_gen(file: IO, func: DocFunc):
        doc = func.doc
        if not doc:
            return
        sig = escapemd(str(func.sig))
        print("####", escapemd("." + func.name) + sig, file=file)
        print(doc, file=file)
        print(file=file)

    @staticmethod
    def __should_doc(obj):
        return getattr(obj, "__autodoc__", True)

    def _class_gen(self, file: IO, dcls: DocCls):
        if not dcls.should_doc:
            return

        show_name = escapemd(dcls.show_name)

        text = dcls.doc
        hash_level = "##"

        tmpio = io.StringIO()
        for func in dcls.funcs:
            self._func_gen(tmpio, func)

        if text or tmpio.getvalue().strip():
            print(f"{hash_level} {show_name}", file=file)
            if text:
                print(text, file=file)
                print("\n", file=file)
            print(tmpio.getvalue(), file=file)

    @staticmethod
    def __show_class_name(class_obj, name):
        params = getattr(class_obj, "__parameters__", None)

        show_name = escapemd(name)
        bases = []
        for base in class_obj.__bases__:
            if base != Generic:
                bases.append(escapemd(base.__name__))
        if bases:
            show_name += "(" + ",".join(bases) + ")"
        if params:
            pnames = []
            for param in params:
                pname = param.__name__
                bound = param.__bound__
                if bound:
                    bound = getattr(
                        bound, "__name__", getattr(bound, "__forward_arg__", "")
                    )
                    pname = escapemd(pname) + "=" + escapemd(bound)
                pnames += [pname]
            show_name = show_name + " [" + ",".join(pnames) + "]"
        return show_name

    def module_gen(self, mod: ModuleType) -> str:
        """Generate markdown, given an imported module with docstring comments.

        Returns: name of the module generated.
        """
        if not self.__should_doc(mod):
            return ""

        docmod = DocMod(mod)

        parentpath = pathlib.Path(os.path.dirname(mod.__file__))
        if not self.source_path:
            log.debug("set source path: %s", parentpath)
            self.source_path = parentpath

        # force doc for top level
        docmod.should_doc = True

        self._module_gen(docmod)

    def _module_gen(self, docmod: DocMod):
        if not docmod.should_doc:
            return

        name = docmod.name

        file = self.__get_output_file(name)

        self.__module_header(file, docmod)

        self.__show_source_link(file, docmod.mod)

        for dmod in docmod.modules:
            self._module_gen(dmod)
            if self.module_links:
                # link to it
                sub_file = self.__module_name_to_md(dmod.name)
                print(f" - [{dmod.name}]({sub_file})", file=file)

        for dcls in docmod.classes:
            self._class_gen(file, dcls)

        if docmod.funcs:
            print("## Functions:\n", file=file)
            for func in docmod.funcs:
                self._func_gen(file, func)

        if file != self.output_fh:
            file.close()

        return name

    def __show_source_link(self, file, mod):
        if self.source_url:
            source_link = (
                self.source_url.strip("/")
                + "/"
                + os.path.relpath(mod.__file__, self.source_path)
            )
            print(f"[(view source)]({source_link})", file=file)


__all__ = ["DocMd"]
