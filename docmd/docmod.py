"""
Python module documentation extraction.
"""
import re
import inspect
import os

import pathlib
import logging as log
import textwrap
from typing import Generic

log.basicConfig()

__autodoc__ = False


def _dedent(doc):
    doc = doc or ""
    doc = doc.strip()
    first_dent = re.match("[^ ][^\n]+\r?\n+( {2,})", doc)
    if first_dent:
        # we assume you mean for the first line to be "dedented" along with the next
        doc = first_dent[1] + doc
    doc = textwrap.dedent(doc)
    return doc


def _get_kids(ent):
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


# pylint: disable=too-few-public-methods
class DocFunc:
    """A documented function."""

    def __init__(self, func, path):
        self.path = path
        self.name = func.__name__
        self.doc = _dedent(getattr(func, "__doc__"))
        self.sig = inspect.signature(func)
        self.should_doc = getattr(func, "__autodoc__", True) and self.doc


class DocCls:
    """A documented class."""

    def __init__(self, class_obj, name):
        self.name = name
        self.show_name = self.__show_class_name(class_obj, name)
        self.doc = _dedent(getattr(class_obj, "__doc__"))
        self.funcs = []

        for path, ent in _get_kids(class_obj):
            if inspect.isfunction(ent):
                self.funcs.append(DocFunc(ent, name + "." + path))

        has_docs = self.doc or any(obj.should_doc for obj in self.funcs)

        self.should_doc = getattr(class_obj, "__autodoc__", True) and has_docs

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


class DocMod:
    """A documented module."""

    def __init__(self, mod, seen=None):
        self.name = mod.__name__
        self.doc = _dedent(getattr(mod, "__doc__"))
        self.mod = mod
        self.classes = []
        self.modules = []
        self.funcs = []
        seen = seen or set()
        self.__walk(seen)
        has_docs = (
            self.doc
            or any(
                obj.should_doc for obj in (*self.classes, *self.modules, *self.funcs)
            )
            or self.funcs
        )
        self.should_doc = getattr(mod, "__autodoc__", True) and has_docs

    def __walk(self, seen):
        parent_path = pathlib.Path(os.path.dirname(self.mod.__file__))
        for path, ent in _get_kids(self.mod):
            if ent in seen:
                continue

            if inspect.isclass(ent) and ent.__module__ == self.mod.__name__:
                seen.add(ent)
                self.__add_class(ent, path)

            if (
                inspect.isfunction(ent)
                and ent.__module__ == self.mod.__name__
                and getattr(ent, "__doc__")
            ):
                seen.add(ent)
                self.funcs.append(DocFunc(ent, path))

            if inspect.ismodule(ent):
                filepath = getattr(ent, "__file__", "")
                childpath = pathlib.Path(filepath)

                if parent_path in childpath.parents:
                    # generate submodule
                    seen.add(ent)
                    self.modules.append(DocMod(ent, seen=seen))

    def __add_class(self, class_obj, name):
        self.classes.append(DocCls(class_obj, name))


__all__ = ["DocMod"]
