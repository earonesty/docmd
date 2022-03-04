"""test: module docstring"""
import importlib
import io
import sys
import textwrap
import types
from typing import TypeVar, Generic

from docmd import DocMd
from docmd.__main__ import main


def import_code(code, name):
    # create blank module
    code = textwrap.dedent(code)
    module = types.ModuleType(name)
    # populate the module with code
    exec(code, module.__dict__)
    module.__file__ = __file__
    return module


def test_basic():
    mod = import_code(
        """
    '''Docstring for module'''
    import sys
    
    class Foo:
        '''Docstring for foo class
        
        Second line'''
        
        def meth1(arg, kw1=None):
            '''
            Best meth1
            '''
    """,
        "foomod",
    )

    out = io.StringIO()
    dmd = DocMd(output_fh=out)
    dmd.module_gen(mod)
    res = out.getvalue()
    assert "Docstring for module" in res
    assert "Docstring for foo class" in res
    assert "kw1" in res
    assert "arg" in res
    assert "sys" not in res
    assert "Second line" in res
    assert "foomod" in res


def test_output_dir(tmp_path):
    """test: output dir"""
    mod = sys.modules[__name__]
    dmd = DocMd(output_dir=tmp_path)
    dmd.module_gen(mod)
    dirlist = list(tmp_path.iterdir())
    assert len(dirlist) == 1
    assert dirlist[0].name == __name__ + ".md"
    res = dirlist[0].open("r").read()
    assert "test: output dir" in res
    assert "Functions" in res


def test_funcs_hidden():
    mod = import_code(
        """
    class Foo:
        def undocumented():
            pass
        
    def undocumented():
        pass
        
    """,
        "foomod",
    )

    out = io.StringIO()
    dmd = DocMd(output_fh=out)
    dmd.module_gen(mod)
    res = out.getvalue()
    assert "foomod" in res
    assert "undocumented" not in res


def test_main(capsys):
    """test: main docgen"""

    sys.argv = ["ack", __name__]
    main()
    captured = capsys.readouterr()
    assert "test: main docgen" in captured.out


def test_main_arg(capsys, caplog):
    """test: main docgen url"""
    sys.argv = ["ack", __name__, "-u", "https://somecoderepo"]
    main()
    captured = capsys.readouterr()
    assert not caplog.records
    assert "test: main docgen" in captured.out
    assert f"somecoderepo/{__name__}.py" in captured.out


def test_main_debug(caplog):
    """test: main docgen url"""
    sys.argv = ["ack", __name__, "-u", "https://somecoderepo", "--debug"]
    main()
    captured = caplog.records
    assert any("set source path" in rec.message for rec in captured)


def test_sub_link():
    mod = importlib.import_module("docmd")
    out = io.StringIO()
    dmd = DocMd(output_fh=out)
    dmd.module_gen(mod)
    out = out.getvalue()
    assert "[docmd](#docmd).docmd" in out


def test_multifile_link(tmp_path):
    mod = importlib.import_module("docmd")
    dmd = DocMd(output_dir=tmp_path)
    dmd.module_gen(mod)
    out = (tmp_path / "docmd.md").open("r").read()
    assert "[docmd.docmd](docmd_docmd.md)" in out
    sub = (tmp_path / "docmd_docmd.md").open("r").read()
    assert "[docmd](docmd.md).docmd" in sub


def test_skip_multi():
    """test: see once"""
    mod = sys.modules[__name__]
    out = io.StringIO()
    dmd = DocMd(output_fh=out)
    dmd.module_gen(mod)
    # prevent someone from breaking the test
    assert should_skip_this == test_skip_multi
    assert out.getvalue().count("test: see once") == 1


should_skip_this = test_skip_multi


def test_skip_noauto():
    mod = import_code(
        """
    '''nodoc'''
    __autodoc__ = False
    class Foo:
        pass
    """,
        "foomod",
    )
    out = io.StringIO()
    dmd = DocMd(output_fh=out)
    dmd.module_gen(mod)
    assert not out.getvalue()


def test_skip_classes():
    mod = import_code(
        """
    '''nodoc'''
    class Foo:
        '''doc foo'''
    
    class Bar:
        __autodoc__ = False
        '''doc bar'''
        
    class Baz:
        '''doc baz'''       
    """,
        "foomod",
    )
    out = io.StringIO()
    dmd = DocMd(output_fh=out)
    dmd.module_gen(mod)
    assert "Bar" not in out.getvalue()
    assert "Foo" in out.getvalue()
    assert "Baz" in out.getvalue()


T1 = TypeVar(name="T1", bound="int")
T2 = TypeVar(name="T2", bound=int)


# forward ref
class Typed1(Generic[T1]):
    """test: typed class"""

    def method(self) -> T1:
        """test: return bound"""


# bound to type
class Typed2(Generic[T2]):
    """test: typed class"""

    def method(self) -> T2:
        """test: return bound"""


def test_generic_bound_type():
    mod = sys.modules[__name__]
    out = io.StringIO()
    dmd = DocMd(output_fh=out)
    dmd.module_gen(mod)
    assert "Typed1 [T1=int]" in out.getvalue()
    assert "Typed2 [T2=int]" in out.getvalue()
