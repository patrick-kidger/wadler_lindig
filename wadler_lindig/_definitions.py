import contextlib
import dataclasses
import difflib
import functools as ft
import sys
import types
import typing
from collections.abc import Callable, Iterable, Sequence
from typing import (
    Any,
    Generic,
    Literal,
    NamedTuple,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from ._wadler_lindig import (
    AbstractDoc,
    BreakDoc,
    ConcatDoc,
    TextDoc,
    pformat_doc,
)


class _WithRepr:
    def __init__(self, string: str):
        self.string = string

    def __repr__(self) -> str:
        return self.string


def array_summary(shape: tuple[int, ...], dtype: str, kind: None | str) -> TextDoc:
    """Summarises an array based on its shape/dtype/kind. (Where 'kind' refers to NumPy
    vs PyTorch vs JAX etc.)

    **Arguments:**

    - `shape`: a tuple of integers.
    - `dtype`: a string, for which common dtypes will be contracted (`float -> f`,
        `uint -> u`, `int -> i`, `complex -> c`)
    - `kind`: optional. If provided it is written in brackets afterwards.

    **Returns:**

    A [`wadler_lindig.TextDoc`][] with text looking like e.g. `f32[2,3,4](numpy)` for a
    NumPy array of shape `(2, 3, 4)` and `float32` dtype.
    """
    short_dtype = (
        dtype.replace("float", "f")
        .replace("uint", "u")
        .replace("int", "i")
        .replace("complex", "c")
    )
    short_shape = ",".join(map(str, shape))
    out = f"{short_dtype}[{short_shape}]"
    if kind is not None:
        out = out + f"({kind})"
    return TextDoc(out)


def bracketed(
    begin: AbstractDoc,
    docs: Sequence[AbstractDoc],
    sep: AbstractDoc,
    end: AbstractDoc,
    indent: int,
) -> AbstractDoc:
    """A helper for formatting a 'bracketed' object: tuples, lists, classes, etc, which
    are all represented in essentially similar ways: a pair of brackets (whether round,
    square, etc.), a sequence of values in between -- which are indented if laid out in
    vertical mode, and possibly a name as prefix.

    See the [`(break-group).nest-break` example](./pattern.ipynb) for more on the
    pattern that this enables.

    **Arguments:**

    - `begin`: appears at the start, before any indent.
    - `docs:`: a sequence of documents. They will either be laid out horizontally
        together or vertically together.
    - `sep`: each element of `docs` will be separated by `sep`.
    - `end`: appears at the end, after any indent.
    - `indent`: how much to indent (for [`wadler_lindig.NestDoc`][] to use) when laying
        out vertically.

    **Returns:**

    A document in `(break-group).nest-break` form.

    !!! example

        Formatting a list, which do not have any name prefix:
        ```python
        import wadler_lindig as wl

        wl.bracketed(
            begin=wl.TextDoc("["),
            docs=[wl.pdoc(x) for x in obj],
            sep=wl.comma,
            end=wl.TextDoc("]"),
            indent=indent,
        )
        ```

        Formatting a frozenset, which does have a name prefix:
        ```python
        import wadler_lindig as wl

        wl.bracketed(
            begin=wl.TextDoc("frozenset({"),
            docs=[wl.pdoc(x) for x in obj],
            sep=wl.comma,
            end=wl.TextDoc("})"),
            indent=indent,
        )
        ```
    """
    if len(docs) == 0:
        return (begin + end).group()
    else:
        docs = [x.group() for x in docs]
        nested = (BreakDoc("") + join(sep, docs).group()).nest(indent) + BreakDoc("")
        return (begin + nested + end).group()


def join(sep: AbstractDoc, docs: Sequence[AbstractDoc]) -> AbstractDoc:
    """Concatenates `objs` together separated by `sep`.

    **Arguments:**

    - `sep`: the separate to use.
    - `docs`: a sequence of documents to join.

    **Returns:**

    `ConcatDoc(docs[0], sep, docs[1], sep, docs[2], ..., sep, docs[-1])`
    """
    if len(docs) == 0:
        return ConcatDoc()
    pieces = [docs[0]]
    for obj in docs[1:]:
        pieces.append(sep)
        pieces.append(obj)
    return ConcatDoc(*pieces)


def named_objs(pairs: Iterable[tuple[str, Any]], **kwargs) -> list[AbstractDoc]:
    """Formats key-value pairs in the form 'key=value'.

    **Arguments:**

    - `pairs`: an iterable of `(key, value)` pairs.
    - `**kwargs`: passed on to each `pdoc(value, **kwargs)`

    **Returns:**

    A list of documents `TextDoc(key) + TextDoc("=") + pdoc(value, **kwargs)` for each
    key-value pair.
    """
    return [TextDoc(key) + TextDoc("=") + pdoc(value, **kwargs) for key, value in pairs]


comma: AbstractDoc = TextDoc(",") + BreakDoc(" ")
if getattr(typing, "GENERATING_DOCUMENTATION", "") == "wadler-lindig":
    # Needed to have mkdocstrings not crash :D
    object.__setattr__(comma, "__module__", __name__)
    object.__setattr__(
        comma, "__doc__", """A shorthand for `TextDoc(',') + BreakDoc(' ')`."""
    )


def _pformat_list(obj: list, **kwargs) -> AbstractDoc:
    return bracketed(
        begin=TextDoc("["),
        docs=[pdoc(x, **kwargs) for x in obj],
        sep=comma,
        end=TextDoc("]"),
        indent=kwargs["indent"],
    )


def _pformat_set(obj: set, **kwargs) -> AbstractDoc:
    return bracketed(
        begin=TextDoc("{"),
        docs=[pdoc(x, **kwargs) for x in obj],
        sep=comma,
        end=TextDoc("}"),
        indent=kwargs["indent"],
    )


def _pformat_frozenset(obj: frozenset, **kwargs) -> AbstractDoc:
    return bracketed(
        begin=TextDoc("frozenset({"),
        docs=[pdoc(x, **kwargs) for x in obj],
        sep=comma,
        end=TextDoc("})"),
        indent=kwargs["indent"],
    )


def _pformat_tuple(obj: tuple, **kwargs) -> AbstractDoc:
    if len(obj) == 1:
        objs = [pdoc(obj[0], **kwargs) + TextDoc(",")]
    else:
        objs = [pdoc(x, **kwargs) for x in obj]
    return bracketed(
        begin=TextDoc("("),
        docs=objs,
        sep=comma,
        end=TextDoc(")"),
        indent=kwargs["indent"],
    )


def _pformat_namedtuple(obj: NamedTuple, **kwargs) -> AbstractDoc:
    objs = named_objs([(name, getattr(obj, name)) for name in obj._fields], **kwargs)
    return bracketed(
        begin=TextDoc(obj.__class__.__name__ + "("),
        docs=objs,
        sep=comma,
        end=TextDoc(")"),
        indent=kwargs["indent"],
    )


def _dict_entry(key: Any, value: Any, **kwargs) -> AbstractDoc:
    return pdoc(key, **kwargs) + TextDoc(":") + BreakDoc(" ") + pdoc(value, **kwargs)


def _pformat_dict(obj: dict, **kwargs) -> AbstractDoc:
    objs = [_dict_entry(key, value, **kwargs) for key, value in obj.items()]
    return bracketed(
        begin=TextDoc("{"),
        docs=objs,
        sep=comma,
        end=TextDoc("}"),
        indent=kwargs["indent"],
    )


def _array_kind(x) -> None | str:
    # For pragmatic reasons we ship with support for NumPy + PyTorch + JAX out of the
    # box.
    for module, array in [
        ("numpy", "ndarray"),
        ("torch", "Tensor"),
        ("jax", "Array"),
        ("mlx.core", "array"),
    ]:
        if module in sys.modules and isinstance(x, getattr(sys.modules[module], array)):
            return module
    return None


def _pformat_ndarray(obj, **kwargs) -> AbstractDoc:
    short_arrays = kwargs["short_arrays"]
    if short_arrays:
        kind = _array_kind(obj)
        assert kind is not None
        *_, dtype = str(obj.dtype).rsplit(".")
        return array_summary(obj.shape, dtype, kind)
    return TextDoc(repr(obj))


def _pformat_partial(obj: ft.partial, **kwargs) -> AbstractDoc:
    objs = (
        [pdoc(obj.func, **kwargs)]
        + [pdoc(x, **kwargs) for x in obj.args]
        + named_objs(obj.keywords.items(), **kwargs)
    )
    return bracketed(
        begin=TextDoc("partial("),
        docs=objs,
        sep=comma,
        end=TextDoc(")"),
        indent=kwargs["indent"],
    )


def _pformat_function(
    obj: types.FunctionType, *, show_function_module: bool, **kwargs
) -> AbstractDoc:
    del kwargs
    if hasattr(obj, "__wrapped__"):
        fn = "wrapped function"
    else:
        fn = "function"
    if show_function_module:
        name = f"{obj.__module__}.{obj.__qualname__}"
    else:
        name = obj.__qualname__
    return TextDoc(f"<{fn} {name}>")


def _pformat_dataclass(obj, **kwargs) -> AbstractDoc:
    type_name = "_" + type(obj).__name__
    uninitialised = _WithRepr("<uninitialised>")
    objs = []
    for field in dataclasses.fields(obj):
        if field.repr:
            value = getattr(obj, field.name, uninitialised)
            if not (kwargs["hide_defaults"] and value is field.default):
                objs.append((field.name.removeprefix(type_name), value))
    objs = named_objs(objs, **kwargs)
    name_kwargs = kwargs.copy()
    name_kwargs["show_type_module"] = kwargs["show_dataclass_module"]
    return bracketed(
        begin=pdoc(obj.__class__, **name_kwargs) + TextDoc("("),
        docs=objs,
        sep=comma,
        end=TextDoc(")"),
        indent=kwargs["indent"],
    )


def _pformat_union(obj, **kwargs) -> AbstractDoc:
    bar = BreakDoc(" ") + TextDoc("| ")
    docs = [pdoc(x, **kwargs) for x in get_args(obj)]
    return join(bar, docs)


def _pformat_generic_alias(obj, **kwargs) -> AbstractDoc:
    docs = [pdoc(x, **kwargs) for x in get_args(obj)]
    return bracketed(
        begin=pdoc(get_origin(obj), **kwargs) + TextDoc("["),
        docs=docs,
        sep=comma,
        end=TextDoc("]"),
        indent=kwargs["indent"],
    )


def _pformat_type(obj: type, *, show_type_module: bool, **kwargs) -> AbstractDoc:
    del kwargs
    if hasattr(obj, "__module__") and hasattr(obj, "__qualname__"):
        if not show_type_module or obj.__module__ in (
            "builtins",
            "typing",
            "typing_extensions",
            "collections.abc",
        ):
            return TextDoc(obj.__qualname__)
        else:
            return TextDoc(f"{obj.__module__}.{obj.__qualname__}")
    else:
        # Not sure if it's possible to end up here under normal circumstances.
        return TextDoc(repr(obj))


_T = TypeVar("_T")


class _Foo(Generic[_T]):
    pass


_union_types = (types.UnionType, type(Union[bool, str]))
_generic_alias_types = (types.GenericAlias, type(_Foo[int]))
_type_types = (type, type(Literal))
del _Foo, _T


@contextlib.contextmanager
def _seen_context(seen, obj):
    id_ = id(obj)
    seen.add(id_)
    try:
        yield
    finally:
        seen.remove(id_)


def _none(_):
    return None


def pdoc(
    obj: Any,
    indent: int = 2,
    short_arrays: bool = True,
    custom: Callable[[Any], None | AbstractDoc] = _none,
    hide_defaults: bool = True,
    show_type_module: bool = True,
    show_dataclass_module: bool = False,
    show_function_module: bool = False,
    seen_ids: None | set[int] = None,
    **kwargs,
) -> AbstractDoc:
    """Formats an object into a Wadler–Lindig document. Such documents are essentially
    strings that haven't yet been pretty-formatted to a particular width.

    **Arguments:**

    - `obj`: the object to pretty-doc.
    - `indent`: when the contents of a structured type are too large to fit on one line,
        they will be indented by this amount and placed on separate lines.
    - `short_arrays`: whether to print a NumPy array / PyTorch tensor / JAX array as a
        short summary of the form `f32[3,4]` (here indicating a `float32` matrix of
        shape `(3, 4)`)
    - `custom`: a way to pretty-doc custom types. This will be called on every object it
        encounters. If its return is `None` then the usual behaviour will be performed.
        If its return is an `AbstractDoc` then that will be used instead.
    - `hide_defaults`: whether to show the default values of dataclass fields.
    - `show_type_module`: whether to show the name of the module for a type:
         `somelib.SomeClass` versus `SomeClass`.
    - `show_dataclass_module`: whether to show the name of the module for a dataclass
         instance: `somelib.SomeClass()` versus `SomeClass()`.
    - `show_function_module`: whether to show the name of the module for a function:
         `<function some_fn>` versus `<function somelib.some_fn>`.
    - `seen_ids`: the `id(...)` of any Python objects that have already been seen, and
        should not be further introspected to avoid recursion errors (e.g.
        `x = []; x.append(x)`). Note that for efficiency, this argument will be mutated
        with the ids encountered.
    - `**kwargs`: all kwargs are forwarded on to all `__pdoc__` calls, as an
        escape hatch for custom behaviour.

    **Returns:**

    A pretty-doc representing `obj`.

    !!! info

        The behaviour of this function can be customised in two ways.

        First, any object which implements a
        `__pdoc__(self, **kwargs) -> None | AbstractDoc` method will have that method
        called to determine its pretty-doc.

        Second, the `custom` argument to this function can be used. This is particularly
        useful to provide custom pretty-docs for objects provided by third-party
        libraries. (For which you cannot add a `__pdoc__` method yourself.)
    """

    if seen_ids is None:
        seen_ids = set()

    if id(obj) in seen_ids:
        return TextDoc("<recursive>")

    if isinstance(obj, AbstractDoc):
        return obj

    kwargs["indent"] = indent
    kwargs["short_arrays"] = short_arrays
    kwargs["custom"] = custom
    kwargs["hide_defaults"] = hide_defaults
    kwargs["seen_ids"] = seen_ids
    kwargs["show_type_module"] = show_type_module
    kwargs["show_dataclass_module"] = show_dataclass_module
    kwargs["show_function_module"] = show_function_module

    with _seen_context(seen_ids, obj):
        maybe_custom = custom(obj)
        if maybe_custom is not None:
            return maybe_custom

        if hasattr(type(obj), "__pdoc__"):
            custom_pp = obj.__pdoc__(**kwargs)
            if isinstance(custom_pp, AbstractDoc):
                return custom_pp.group()
            # else it's some non-pretty-print `__pdoc__` method; ignore.

        if obj is None or obj is types.NoneType:
            return TextDoc("None")
        if isinstance(obj, tuple):
            if hasattr(obj, "_fields"):
                return _pformat_namedtuple(cast(NamedTuple, obj), **kwargs)
            return _pformat_tuple(obj, **kwargs)
        if isinstance(obj, list):
            return _pformat_list(obj, **kwargs)
        if isinstance(obj, dict):
            return _pformat_dict(obj, **kwargs)
        if isinstance(obj, set):
            return _pformat_set(obj, **kwargs)
        if isinstance(obj, frozenset):
            return _pformat_frozenset(obj, **kwargs)
        if isinstance(obj, ft.partial):
            return _pformat_partial(obj, **kwargs)
        if isinstance(obj, types.FunctionType):
            return _pformat_function(obj, **kwargs)
        if obj is Any:
            return TextDoc("Any")
        if isinstance(obj, _union_types):
            return _pformat_union(obj, **kwargs)
        # The generic alias check has to come last as unions evaluate true for this one.
        if isinstance(obj, _generic_alias_types):
            return _pformat_generic_alias(obj, **kwargs)
        if isinstance(obj, _type_types):
            return _pformat_type(obj, **kwargs)
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return _pformat_dataclass(obj, **kwargs)
        if _array_kind(obj) is not None:
            return _pformat_ndarray(obj, **kwargs)
        if obj is ...:
            return TextDoc("...")
        # str, bool, int, float, complex etc.
        return TextDoc(repr(obj))


def pformat(
    obj: Any,
    *,
    width: int = 88,
    indent: int = 2,
    short_arrays: bool = True,
    custom: Callable[[Any], None | AbstractDoc] = _none,
    hide_defaults: bool = True,
    show_type_module: bool = True,
    show_dataclass_module: bool = False,
    show_function_module: bool = False,
    **kwargs,
) -> str:
    """As [`wadler_lindig.pprint`][], but returns a string instead of printing to
    stdout.
    """

    doc = pdoc(
        obj,
        indent=indent,
        short_arrays=short_arrays,
        custom=custom,
        hide_defaults=hide_defaults,
        show_type_module=show_type_module,
        show_dataclass_module=show_dataclass_module,
        show_function_module=show_function_module,
        **kwargs,
    )
    return pformat_doc(doc, width)


def pprint(
    obj: Any,
    *,
    width: int = 88,
    indent: int = 2,
    short_arrays: bool = True,
    custom: Callable[[Any], None | AbstractDoc] = _none,
    hide_defaults: bool = True,
    show_type_module: bool = True,
    show_dataclass_module: bool = False,
    show_function_module: bool = False,
    **kwargs,
) -> None:
    """Pretty-prints an object to stdout.

    **Arguments:**

    - `obj`: the object to pretty-print.
    - `width`: a best-effort maximum width to allow. May be exceeded if there are
        unbroken pieces of text which are wider than this.
    - `indent`: when the contents of a structured type are too large to fit on one line,
        they will be indented by this amount and placed on separate lines.
    - `short_arrays`: whether to print a NumPy array / PyTorch tensor / JAX array as a
        short summary of the form `f32[3,4]` (here indicating a `float32` matrix of
        shape `(3, 4)`)
    - `custom`: a way to pretty-print custom types. This will be called on every object
        it . If its return is `None` then the default behaviour will be performed. If
        its return is an [`wadler_lindig.AbstractDoc`][] then that will be used instead.
    - `hide_defaults`: whether to show the default values of dataclass fields.
    - `show_type_module`: whether to show the name of the module for a type:
         `somelib.SomeClass` versus `SomeClass`.
    - `show_dataclass_module`: whether to show the name of the module for a dataclass
         instance: `somelib.SomeClass()` versus `SomeClass()`.
    - `show_function_module`: whether to show the name of the module for a function:
         `<function some_fn>` versus `<function somelib.some_fn>`.
    - `**kwargs`: all other unrecognized kwargs are forwarded on to any `__pdoc__`
        methods encountered, as an escape hatch for custom behaviour.

    **Returns:**

    A string representing `obj`.

    !!! info

        The behaviour of this function can be customised in two ways.

        First, any object which implements a
        `__pdoc__(self, **kwargs) -> None | AbstractDoc` method will have that method
        called to determine its pretty-doc.

        Second, the `custom` argument to this function can be used. This is particularly
        useful to provide custom pretty-docs for objects provided by third-party
        libraries. (For which you cannot add a `__pdoc__` method.)
    """

    print(
        pformat(
            obj,
            width=width,
            indent=indent,
            short_arrays=short_arrays,
            custom=custom,
            hide_defaults=hide_defaults,
            show_type_module=show_type_module,
            show_dataclass_module=show_dataclass_module,
            show_function_module=show_function_module,
            **kwargs,
        )
    )


def pdiff(minus: str, plus: str) -> str:
    """Returns a pretty-diff between two strings.

    (This is just a thin wrapper around the builtin `difflib`, and is just here as a
    helper for common use-cases.)

    !!! example

        ```python
        minus = "hello\\nthere\\nobi wan kenobi"
        plus = "hello\\nthere\\npatrick kidger"
        print(wadler_lindig.pdiff(minus, plus))
        #   hello
        #   there
        # - obi wan kenobi
        # + patrick kidger
        ```

    **Arguments:**

    - `minus`: any lines unique to this string will be prefixed with a `-`.
    - `plus`: any lines unique to this string will be prefixed with a `+`.

    **Returns:**

    A diff between the two tsrings `minus` and `plus`, showing their shared lines once
    and the unique lines from each.
    """
    diff = difflib.ndiff(minus.splitlines(), plus.splitlines())
    diff = "\n".join(line for line in diff if not line.startswith("?"))
    return diff
