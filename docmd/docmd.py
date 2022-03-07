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
import re
import sys
import importlib
import inspect
import os

import pathlib
import logging as log
import textwrap
from types import ModuleType
from typing import IO, Generic

log.basicConfig()

__autodoc__ = False


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
        self.seen = set()
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

    @staticmethod
    def __dedent(doc):
        first_dent = re.match("[^ ][^\n]+\r?\n+( {2,})", doc)
        if first_dent:
            # we assume you mean for the first line to be "dedented" along with the next
            doc = first_dent[1] + doc
        doc = textwrap.dedent(doc)
        return doc

    def __module_header(self, file: IO, name: str, text: str):
        hash_level = "#" * 1
        if "." in name:
            # link back to top
            parent_name, child_name = name.rsplit(".", 1)
            if self.module_links:
                parent_link = self.__module_name_to_md(parent_name)
                print(
                    f"{hash_level} [{parent_name}]({parent_link}).{child_name}",
                    file=file,
                )
            else:
                parent_link = "#" + parent_name.replace(".", "_")
                print(
                    f"{hash_level} [{parent_name}]({parent_link}).{child_name}",
                    file=file,
                )
        else:
            # top level module
            print(f"{hash_level} {name}", file=file)

        if text and text.strip():
            print(self.__dedent(text), file=file)
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

    def _func_gen(self, file: IO, func, path):
        doc = getattr(func, "__doc__")
        if not doc:
            return
        sig = inspect.signature(func)
        print("####", path + str(sig), file=file)
        print(self.__dedent(doc), file=file)
        print(file=file)

    @staticmethod
    def __should_doc(obj):
        return getattr(obj, "__autodoc__", True)

    def _class_gen(self, file: IO, class_obj, name):
        if not self.__should_doc(class_obj):
            return

        show_name = self.__show_class_name(class_obj, name)

        text = getattr(class_obj, "__doc__")
        hash_level = "##"

        tmpio = io.StringIO()
        for path, ent in self.__get_kids(class_obj):
            if inspect.isfunction(ent):
                self._func_gen(tmpio, ent, "." + path)

        if text or tmpio.getvalue().strip():
            print(f"{hash_level} {show_name}", file=file)
            if text:
                print(self.__dedent(text), file=file)
                print("\n", file=file)
            print(tmpio.getvalue(), file=file)

    @staticmethod
    def __show_class_name(class_obj, name):
        params = getattr(class_obj, "__parameters__", None)

        show_name = name
        bases = []
        for base in class_obj.__bases__:
            if base != Generic:
                bases.append(base.__name__)
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
                    pname = pname + "=" + bound
                pnames += [pname]
            show_name = show_name + " [" + ",".join(pnames) + "]"
        return show_name

    @staticmethod
    def __is_submod(sub, par):
        return sub.startswith(par + ".")

    def module_gen(self, mod: ModuleType) -> str:
        """Generate markdown, given an imported module with docstring comments.

        Returns: name of the module generated.
        """
        if not self.__should_doc(mod):
            return ""

        parentpath = pathlib.Path(os.path.dirname(mod.__file__))
        if not self.source_path:
            log.debug("set source path: %s", parentpath)
            self.source_path = parentpath

        name = mod.__name__

        file = self.__get_output_file(name)

        mod_doc = getattr(mod, "__doc__")

        self.__module_header(file, name, mod_doc)

        self.__show_source_link(file, mod)

        funcs = []

        for path, ent in self.__get_kids(mod):
            if ent in self.seen:
                continue
            log.debug("mod: %s, kid: %s", name, path)
            if inspect.isclass(ent) and self.__is_submod(ent.__module__, mod.__name__):
                # this class is accessible at a parent level
                self.__import_up(ent, mod.__name__)

            if inspect.isclass(ent) and ent.__module__ == mod.__name__:
                self.seen.add(ent)
                self._class_gen(file, ent, path)

            if (
                inspect.isfunction(ent)
                and ent.__module__ == mod.__name__
                and getattr(ent, "__doc__")
            ):
                self.seen.add(ent)
                funcs.append((path, ent))

            if inspect.ismodule(ent):
                filepath = getattr(ent, "__file__", "")
                childpath = pathlib.Path(filepath)
                if parentpath in childpath.parents:
                    # generate submodule
                    self.seen.add(ent)
                    sub_name = self.module_gen(ent)

                    # link to it
                    if sub_name and self.module_links:
                        sub_file = self.__module_name_to_md(sub_name)
                        print(f" - [{sub_name}]({sub_file})", file=file)

        if funcs:
            print("## Functions:\n", file=file)
            for path, ent in funcs:
                self._func_gen(file, ent, path)

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
