"""An improved Wadler–Lindig pretty printer.

This implementation additionally:

- handles new lines in the text to format.
- removes some dead code from the canonical implementation.

References:

(1) Wadler, P., 1998. A prettier printer.
    Journal of Functional Programming, pp.223-244.
(2) Lindig, C. 2000. Strictly Pretty.
    https://lindig.github.io/papers/strictly-pretty-2000.pdf

Inspired by JAX's use of the same references above, but re-implemented from scratch.
"""

from dataclasses import dataclass

from ._ansi import ansi_strip


class AbstractDoc:
    """Base class for all document types.

    For more on the following shorthand methods, see
    [the methods example](./methods.ipynb).
    """

    def __add__(self, other: "AbstractDoc") -> "ConcatDoc":
        """`doc1 + doc2` offers a convenient shorthand for `ConcatDoc(doc1, doc2)`."""
        return ConcatDoc(self, other)

    def nest(self, indent: int) -> "NestDoc":
        """`doc.nest(indent)` offers a convenient shorthand for
        `NestDoc(doc, indent)`.
        """
        return NestDoc(self, indent=indent)

    def group(self) -> "GroupDoc":
        """`doc.group()` offers a convenient shorthand for `GroupDoc(doc)`."""
        return GroupDoc(self)


@dataclass(frozen=True)
class TextDoc(AbstractDoc):
    """Represents an unbroken piece of text to display. May include newlines."""

    text: str


TextDoc.__init__.__doc__ = """**Arguments:**

- `text`: the string of text.
"""


@dataclass(frozen=True)
class BreakDoc(AbstractDoc):
    """If in vertical mode then this is a valid place to insert a newline. If in
    horizontal mode then `self.text` will be displayed instead.
    """

    text: str

    def __post_init__(self):
        if "\n" in self.text:
            raise ValueError("Cannot have newlines in BreakDocs.")


BreakDoc.__init__.__doc__ = """**Arguments:**

- `text`: the string of text to display if a newline is not inserted.
    Common values are `" "` (for example between elements of a list) or `""` (for
    example between the final element of a list and a closing ']').
"""


@dataclass(frozen=True)
class ConcatDoc(AbstractDoc):
    """Concatenate multiple documents together, to be displayed one after another.

    If for example these consist only of `TextDoc`s and other `ConcatDoc`s then there is
    no implied breaking between them, so the formatted text may exceed the maximum
    width. You may wish to separate pieces with `BreakDoc`s to indicate this, for
    example.
    """

    children: tuple[AbstractDoc, ...]

    # Allow calling via both `ConcatDoc(foo, bar, baz)` for convenience, or
    # `ConcatDoc(children=(foo, bar, baz))` for consistency with its repr.
    def __init__(self, *args, children=None):
        if len(args) > 0 and children is None:
            children = args
        elif len(args) > 0 or children is None:
            raise ValueError(
                "Must be called as either `ConcatDoc(children=(foo, bar, ...))` or as "
                "`ConcatDoc(foo, bar, ...)` or as `foo + bar + ...`."
            )
        object.__setattr__(self, "children", children)

    def __add__(self, other: AbstractDoc) -> "ConcatDoc":
        # Slightly fewer nested `ConcatDoc`s when used associatively: `a + b + c`.
        return ConcatDoc(*self.children, other)


ConcatDoc.__init__.__doc__ = """**Arguments:**

Can be called as any of:

- `ConcatDoc(doc1, doc2, doc3, ...)`
- `ConcatDoc(children=(doc1, doc2, doc3, ...))`
- `doc1 + doc2 + doc3 + ...`
"""


@dataclass(frozen=True)
class NestDoc(AbstractDoc):
    """If in vertical mode, increase the indent after each newline by `indent` whilst
    displaying `child`.
    """

    child: AbstractDoc
    indent: int


NestDoc.__init__.__doc__ = """**Arguments:**

- `child`: the child document to display.
- `indent`: how much to increase the indent.

Frequently `child` will be `ConcatDoc(BreakDoc(""), another_doc)`, so that the first
line of `another_doc` will be indented as much as its later lines. See also the
[The `(break-group).nest-break` example](./pattern.ipynb).
"""


@dataclass(frozen=True)
class GroupDoc(AbstractDoc):
    """Groups the parts of a child document to be laid out all horizontally together or
    all vertically together.

    This decision will persist everywhere outside any child `GroupDoc`s, within which
    their own local rule is used. For example using `[...]` to denote a grouping:
    ```
    [
        foo,
        bar,
        [baz, qux]
    ]
    ```
    then `foo`, `bar` and `[baz, qux]` are laid out vertically, but the sub-group
    `[baz, qux]` is judged to have enough space, and so is laid out horizontally.
    """

    child: AbstractDoc


GroupDoc.__init__.__doc__ = """**Arguments:**

- `child`: the child document to display.
"""


# The implementation in both Lindig and JAX additionally tracks an indent and a mode,
# which both seem to just go entirely unused. We don't include them here.
def _vertical(doc: AbstractDoc, width: int) -> bool:
    todo: list[AbstractDoc] = [doc]
    while len(todo) > 0 and width >= 0:
        match todo.pop():
            case TextDoc(text):
                width -= max(map(len, ansi_strip(text).splitlines()), default=0)
            case BreakDoc(text):
                width -= len(ansi_strip(text))
            case ConcatDoc(children):
                todo.extend(reversed(children))
            case NestDoc(child, _):
                todo.append(child)
            case GroupDoc(child):
                todo.append(child)
            case x:
                assert False, str(x)
    return width < 0


def pformat_doc(doc: AbstractDoc, width: int) -> str:
    """Pretty-formats a document using a Wadler–Lindig pretty-printer.

    **Arguments:**

    - `doc`: a document to pretty-format as a string.
    - `width`: a best-effort maximum width to allow. May be exceeded if there are
        unbroken pieces of text which are wider than this.

    **Returns:**

    A string, corresponding to the pretty-formatted document.

    !!! info

        We extend the canonical Wadler–Lindig implementation with the ability to handle
        multiline text. We also remove what seems to be some dead code from their
        implementation.
    """
    outs: list[str] = []
    width_so_far = 0
    vertical: bool = True
    indent: int = 0
    # Start with a `GroupDoc` so that the first thing we do is check whether we should
    # be in vertical or horizontal layout.
    todo: list[bool | int | AbstractDoc] = [GroupDoc(doc)]
    while len(todo) > 0:
        match todo.pop():
            case bool(vertical2):
                vertical = vertical2
            case int(indent2):
                indent = indent2
            case TextDoc(text):
                outs.append(text.replace("\n", "\n" + " " * width_so_far))
                width_so_far += len(ansi_strip(text.rsplit("\n", 1)[-1]))
            case BreakDoc(text):
                if vertical:
                    outs.append("\n" + " " * indent)
                    width_so_far = indent
                else:
                    outs.append(text)
                    width_so_far += len(ansi_strip(text))
            case ConcatDoc(children):
                todo.extend(reversed(children))
            case NestDoc(child, extra_indent):
                todo.append(indent)
                todo.append(child)
                indent += extra_indent
            case GroupDoc(child):
                if vertical and not _vertical(child, width - width_so_far):
                    # If we are currently in vertical mode but do not need to remain
                    # so, then switch to horizontal mode.
                    todo.append(True)
                    todo.append(child)
                    vertical = False
                else:
                    # Else: either remain in vertical mode or remain in horizontal
                    # mode.
                    todo.append(child)
            case _:
                assert False
    return "".join(outs)
