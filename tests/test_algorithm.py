import dataclasses

import wadler_lindig as wl
from wadler_lindig import TextDoc as Txt, BreakDoc as Brk


def test_lindig():
    # From Section 2 of Lindig's paper.

    doc = (
        Txt("begin")
        + (
            Brk(" ")
            + (Txt("stmt;") + Brk(" ") + Txt("stmt;") + Brk(" ") + Txt("stmt;")).group()
        ).nest(3)
        + Brk(" ")
        + Txt("end")
    ).group()

    out50 = wl.pformat(doc, width=50)
    out25 = wl.pformat(doc, width=25)  # Lindig uses 30, but I think that's a mistake.
    out10 = wl.pformat(doc, width=10)
    assert out50 == "begin stmt; stmt; stmt; end"
    assert (
        out25
        == """begin
   stmt; stmt; stmt;
end"""
    )
    assert (
        out10
        == """begin
   stmt;
   stmt;
   stmt;
end"""
    )


def test_newlines_in_text():
    class Foo:
        def __pdoc__(self, **kwargs):
            del kwargs
            return wl.TextDoc("hello\nthere")

    @dataclasses.dataclass
    class Bar:
        x: list[int | Foo]

    bar = Bar(x=[Foo(), 3, Foo(), Foo()])

    out = wl.pformat(bar, width=50)
    expected_out = """Bar(x=[hello
       there, 3, hello
                 there, hello
                        there])"""
    assert out == expected_out

    out = wl.pformat(bar, width=1)
    expected_out = """Bar(
  x=[
    hello
    there,
    3,
    hello
    there,
    hello
    there
  ]
)"""
    assert out == expected_out