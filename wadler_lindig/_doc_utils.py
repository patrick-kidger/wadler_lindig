import typing

_T = typing.TypeVar("_T")

class _DocType(type):
    pass


def doc_obj(x: _T, doc: str) -> _T:
    if getattr(typing, "GENERATING_DOCUMENTATION", False):
        return _DocType("_", (), dict(__doc__=doc))  # pyright: ignore[reportReturnType]
    else:
        return x
