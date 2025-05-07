import collections.abc
import dataclasses
import functools as ft
import typing

import numpy as np
import pytest
import wadler_lindig as wl


def test_tuple():
    assert wl.pformat((1, 2)) == "(1, 2)"
    assert wl.pformat((1,)) == "(1,)"
    assert wl.pformat(()) == "()"


def test_list():
    assert wl.pformat([1, 2]) == ("[1, 2]")
    assert wl.pformat([1]) == "[1]"
    assert wl.pformat([]) == "[]"


def test_dict():
    assert wl.pformat({"a": 1, "b": 2}) == "{'a': 1, 'b': 2}"
    assert wl.pformat({"a": 1}) == "{'a': 1}"
    assert wl.pformat(dict()) == "{}"


def test_named_tuple():
    class M(typing.NamedTuple):
        a: int

    assert wl.pformat(M(1)) == "M(a=1)"


def test_numpy_array():
    assert wl.pformat(np.array(1)) == "i64[](numpy)"
    assert wl.pformat(np.arange(12).reshape(3, 4)) == "i64[3,4](numpy)"
    assert wl.pformat(np.array(1), short_arrays=False) == "array(1)"


def test_builtins():
    assert wl.pformat(1) == "1"
    assert wl.pformat(0.1) == "0.1"
    assert wl.pformat(True) == "True"
    assert wl.pformat(1 + 1j) == "(1+1j)"
    assert wl.pformat("hi") == "'hi'"


def test_function():
    def f():
        pass

    @ft.wraps(f)
    def g():
        pass

    h = ft.partial(f)

    assert wl.pformat(f) == "<function test_function.<locals>.f>"
    assert wl.pformat(g) == "<wrapped function test_function.<locals>.f>"
    assert wl.pformat(h) == "partial(<function test_function.<locals>.f>)"


@pytest.mark.parametrize("sequence_type", (tuple, list))
@pytest.mark.parametrize("width", (92, 93, 94))
def test_sequence(sequence_type, width):
    input = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do".split(" ")
    input = sequence_type(input)
    output = wl.pformat(input, width=width, indent=1)
    if width == 92:
        expected_output = """
 'Lorem',
 'ipsum',
 'dolor',
 'sit',
 'amet,',
 'consectetur',
 'adipiscing',
 'elit,',
 'sed',
 'do'
"""
    elif width == 93:
        expected_output = (
            "\n"
            " 'Lorem', 'ipsum', 'dolor', 'sit', 'amet,', 'consectetur', 'adipiscing', "
            "'elit,', 'sed', 'do'"
            "\n"
        )
    else:
        expected_output = (
            "'Lorem', 'ipsum', 'dolor', 'sit', 'amet,', 'consectetur', 'adipiscing', "
            "'elit,', 'sed', 'do'"
        )
    if sequence_type is tuple:
        expected_output = f"({expected_output})"
    else:
        expected_output = f"[{expected_output}]"
    assert output == expected_output


@dataclasses.dataclass
class SomeDataclass:
    foo: list[str]


class SomeClass:
    def __pdoc__(self, **kwargs):
        return wl.pdoc(SomeDataclass(["lorem", "ipsum", "dolor sit amet"]), **kwargs)


@dataclasses.dataclass
class MyDataclass:
    x: SomeClass
    y: list[str]
    z: np.ndarray


def test_complicated():
    obj = MyDataclass(x=SomeClass(), y=["foo", "bar"], z=np.arange(12).reshape(3, 4))
    out = wl.pformat(obj, width=20)
    expected_out = """MyDataclass(
  x=SomeDataclass(
    foo=[
      'lorem',
      'ipsum',
      'dolor sit amet'
    ]
  ),
  y=['foo', 'bar'],
  z=i64[3,4](numpy)
)"""
    assert out == expected_out


def test_generic_alias():
    # This has type `types.GenericAlias`...
    x = dict[int, str]
    out = wl.pformat(x, width=1)
    assert (
        out
        == """dict[
  int,
  str
]"""
    )

    # ...but this has a different type.
    T1 = typing.TypeVar("T1")
    T2 = typing.TypeVar("T2")
    T3 = typing.TypeVar("T3")
    T4 = typing.TypeVar("T4")

    class Foo(typing.Generic[T1, T2, T3, T4]):
        pass

    class Bar:
        pass

    foo = Foo[int, typing.Any, collections.abc.Sequence, Bar]
    out = wl.pformat(foo, width=1)
    assert (
        out
        == """tests.test_definitions.test_generic_alias.<locals>.Foo[
  int,
  Any,
  Sequence,
  tests.test_definitions.test_generic_alias.<locals>.Bar
]"""
    )


def test_nested_generic():
    assert wl.pformat(tuple[tuple[int, str]]) == "tuple[tuple[int, str]]"


def test_union():
    # This has type `types.UnionType`...
    assert wl.pformat(int | str) == "int | str"
    assert wl.pformat(int | str | bytes, width=1) == "int\n| str\n| bytes"

    class Foo:
        pass

    # ...but this has a different type.
    x = typing.Union[int, str, Foo]  # noqa: UP007
    expected_out = "int\n| str\n| tests.test_definitions.test_union.<locals>.Foo"
    assert wl.pformat(x, width=1) == expected_out


def test_optional():
    # This has type `types.UnionType`...
    assert wl.pformat(typing.Optional[int], width=1) == "int\n| None"  # noqa: UP007


# Simple case
@dataclasses.dataclass
class Foo:
    number: float
    name: str = "Dummy"


# Nested dataclasses
@dataclasses.dataclass
class Bar:
    foo: Foo
    num: int = 0


# Nonscalar fields
@dataclasses.dataclass
class Baz:
    array: np.ndarray

    def __init__(self, array: np.ndarray):
        self.array = array


def test_hide_defaults():
    """Check if defaults are hidden when show_defaults=False and the default value has
    not been tweaked. (E.g. if the default name is "Dummy" and the user does not pass
    something else.)
    """

    foo = Foo(3.14)
    out = wl.pformat(foo, hide_defaults=False)
    assert out == "Foo(number=3.14, name='Dummy')"

    out = wl.pformat(foo)  # hide_defaults=True
    assert out == "Foo(number=3.14)"

    bar = Bar(Foo(42.0))
    out = wl.pformat(bar, hide_defaults=False)
    assert out == "Bar(foo=Foo(number=42.0, name='Dummy'), num=0)"

    out = wl.pformat(bar)  # hide_defaults=True
    assert out == "Bar(foo=Foo(number=42.0))"

    # Show defaults if tweaked
    foo = Foo(42.0, name="Answer")
    out = wl.pformat(foo)
    assert out == "Foo(number=42.0, name='Answer')"

    baz = Baz(np.ones((3, 4)))
    out = wl.pformat(baz)
    assert out == "Baz(array=f64[3,4](numpy))"

    # Defaults defined in __init__ are currently not recognized as default values for
    # dataclass fields.
    # https://github.com/patrick-kidger/wadler_lindig/pull/3
    # @dataclasses.dataclass
    # class Wrapped:
    #     foo: Foo

    #     # Mismatch attribute and parameter names
    #     def __init__(self, some_foo: Foo = Foo(3.14)):
    #         self.foo = some_foo

    # wrapped = Wrapped()
    # out = wl.pformat(wrapped)
    # assert out == "Wrapped()"  # Will fail


def test_recursive():
    x = []
    x.append(x)
    assert wl.pformat(x) == "[<recursive>]"

    # And in particular that the two identical objects don't count as recursive.
    assert (
        wl.pformat([test_recursive, test_recursive])
        == "[<function test_recursive>, <function test_recursive>]"
    )


def test_literal():
    assert wl.pformat(typing.Literal) == "Literal"
    assert wl.pformat(typing.Literal[1]) == "Literal[1]"
    assert wl.pformat(typing.Literal[1, "foo"]) == "Literal[1, 'foo']"


def test_generic_alias_with_custom():
    T = typing.TypeVar("T")

    class Foo(typing.Generic[T]):
        pass

    def custom(x):
        if x is Foo:
            return wl.TextDoc("Bar")

    assert wl.pformat(Foo, custom=custom) == "Bar"
    assert wl.pformat(Foo[int], custom=custom) == "Bar[int]"
    assert wl.pformat(Foo[Foo[int]], custom=custom) == "Bar[Bar[int]]"


def test_ellipsis():
    assert wl.pformat(...) == "..."
    assert wl.pformat(collections.abc.Callable[..., int]) == "Callable[..., int]"


def test_dataclass_with_custom():
    @dataclasses.dataclass
    class X:
        x: int

    def custom(obj):
        if obj is X:
            return wl.TextDoc("Y")

    assert wl.pformat(X(x=1), custom=custom) == "Y(x=1)"


def test_show_module():
    @dataclasses.dataclass
    class X:
        x: int

    assert (
        wl.pformat(test_show_module, show_function_module=True)
        == f"<function {__name__}.test_show_module>"
    )
    assert (
        wl.pformat(test_show_module, show_function_module=False)
        == "<function test_show_module>"
    )
    assert (
        wl.pformat(X, show_type_module=True)
        == f"{__name__}.test_show_module.<locals>.X"
    )
    assert wl.pformat(X, show_type_module=False) == "test_show_module.<locals>.X"
    assert (
        wl.pformat(X(x=1), show_dataclass_module=True)
        == f"{__name__}.test_show_module.<locals>.X(x=1)"
    )
    assert (
        wl.pformat(X(x=1), show_dataclass_module=False)
        == "test_show_module.<locals>.X(x=1)"
    )
