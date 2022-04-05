import re
import inspect
import os

import pathlib
import logging as log
import textwrap
from typing import Generic

log.basicConfig()


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


class DocFunc:
    def __init__(self, func, path):
        self.path = path
        self.doc = _dedent(getattr(func, "__doc__"))
        self.sig = inspect.signature(func)
        self.should_doc = getattr(func, "__autodoc__", True)


class DocCls:
    def __init__(self, class_obj, name):
        self.name = name
        self.show_name = self.__show_class_name(class_obj, name)
        self.doc = _dedent(getattr(class_obj, "__doc__"))
        self.should_doc = getattr(class_obj, "__autodoc__", True)
        self.funcs = []

        for path, ent in _get_kids(class_obj):
            if inspect.isfunction(ent):
                self.funcs.append(DocFunc(ent, name + "." + path))

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
    def __init__(self, mod, seen=None):
        self.name = mod.__name__
        self.doc = _dedent(getattr(mod, "__doc__"))
        self.should_doc = getattr(mod, "__autodoc__", True)
        self.mod = mod
        self.parent_path = pathlib.Path(os.path.dirname(self.mod.__file__))
        self.seen = seen or set()
        self.classes = []
        self.modules = []
        self.funcs = []
        self._walk()

    def _walk(self):

        for path, ent in _get_kids(self.mod):
            if ent in self.seen:
                continue

            if inspect.isclass(ent) and ent.__module__ == self.mod.__name__:
                self.seen.add(ent)
                self.add_class(ent, path)

            if (
                    inspect.isfunction(ent)
                    and ent.__module__ == self.mod.__name__
                    and getattr(ent, "__doc__")
            ):
                self.seen.add(ent)
                self.funcs.append(DocFunc(ent, path))

            if inspect.ismodule(ent):
                filepath = getattr(ent, "__file__", "")
                childpath = pathlib.Path(filepath)

                if self.parent_path in childpath.parents:
                    # generate submodule
                    self.seen.add(ent)
                    self.modules.append(DocMod(ent, seen=self.seen))

    def add_class(self, class_obj, name):
        self.classes.append(DocCls(class_obj, name))


__all__ = ["DocMod"]
