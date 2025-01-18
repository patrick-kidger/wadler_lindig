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

    assert wl.pformat(f) == "<function f>"
    assert wl.pformat(g) == "<wrapped function f>"
    assert wl.pformat(h) == "partial(<function f>)"


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


def test_complicated():
    @dataclasses.dataclass
    class SomeDataclass:
        foo: list[str]

    class SomeClass:
        def __pdoc__(self, **kwargs):
            return wl.pdoc(
                SomeDataclass(["lorem", "ipsum", "dolor sit amet"]), **kwargs
            )

    @dataclasses.dataclass
    class MyDataclass:
        x: SomeClass
        y: list[str]
        z: np.ndarray

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


def test_union():
    # This has type `types.UnionType`...
    assert wl.pformat(int | str) == "int | str"
    assert wl.pformat(int | str | bytes, width=1) == "int\n| str\n| bytes"

    class Foo:
        pass

    # ...but this has a different type.
    x = typing.Union[int, str, Foo]
    expected_out = "int\n| str\n| tests.test_definitions.test_union.<locals>.Foo"
    assert wl.pformat(x, width=1) == expected_out


def test_optional():
    # This has type `types.UnionType`...
    assert wl.pformat(typing.Optional[int], width=1) == "int\n| None"


def test_hide_defaults():
    """Check if defaults are hidden when show_defaults=False and the default value has
    not been tweaked. (E.g. if the default name is "Dummy" and the user does not pass
    something else.)
    """

    # Simple case
    @dataclasses.dataclass
    class Foo:
        number: float
        name: str = "Dummy"

    foo = Foo(3.14)
    out = wl.pformat(foo, hide_defaults=False)
    assert out == "Foo(number=3.14, name='Dummy')"

    out = wl.pformat(foo)  # hide_defaults=True
    assert out == "Foo(number=3.14)"

    # Nested dataclasses
    @dataclasses.dataclass
    class Bar:
        foo: Foo
        num: int = 0

    bar = Bar(Foo(42.0))
    out = wl.pformat(bar, hide_defaults=False)
    assert out == "Bar(foo=Foo(number=42.0, name='Dummy'), num=0)"

    out = wl.pformat(bar)  # hide_defaults=True
    assert out == "Bar(foo=Foo(number=42.0))"

    # Show defaults if tweaked
    foo = Foo(42.0, name="Answer")
    out = wl.pformat(foo)
    assert out == "Foo(number=42.0, name='Answer')"

    @dataclasses.dataclass
    class Baz:
        array: np.ndarray

        def __init__(self, array: np.ndarray = np.ones((3, 4))):
            self.array = array

    baz = Baz()
    out = wl.pformat(baz)
    assert out == "Baz()"
