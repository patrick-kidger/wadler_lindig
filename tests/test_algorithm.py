import dataclasses

import wadler_lindig as wl
from wadler_lindig import BreakDoc as Brk, TextDoc as Txt


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


class Foo:
    def __pdoc__(self, **kwargs):
        del kwargs
        return wl.TextDoc("hello\nthere")


@dataclasses.dataclass
class Bar:
    x: list[int | Foo]


def test_newlines_in_text():
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


def _tagged_list(tag_width: bool):
    def tag(t):
        return Txt(t, width=tag_width)

    items = [Txt("aaa"), Txt("bbb"), Txt("ccc")]
    body = wl.join(
        Txt(",") + Brk(" "), [tag("<span>") + x + tag("</span>") for x in items]
    )
    return (
        tag("<div>") + Txt("[") + (Brk("") + body).nest(2) + Brk("") + Txt("]")
    ).group()


def test_zero_width_text_matches_plain_layout():
    import re

    items = [Txt("aaa"), Txt("bbb"), Txt("ccc")]
    plain_doc = (
        Txt("[")
        + (Brk("") + wl.join(Txt(",") + Brk(" "), items)).nest(2)
        + Brk("")
        + Txt("]")
    ).group()
    for w in range(1, 30):
        html = wl.pformat(_tagged_list(False), width=w)
        assert re.sub(r"</?\w+>", "", html) == wl.pformat(plain_doc, width=w)


def test_zero_width_text_boundary():
    # "[aaa, bbb, ccc]" is 15 chars; with tags it is much longer.
    assert "\n" not in wl.pformat(_tagged_list(False), width=15)
    assert "\n" in wl.pformat(_tagged_list(True), width=15)


def test_zero_width_text_multiline_and_default():
    doc = (Txt("ab") + Txt("x\ny", width=False) + Txt("cd")).group()
    assert wl.pformat(doc, width=80) == "abx\n  ycd"
    assert Txt("x") == Txt("x", width=True)
    assert Txt("x") != Txt("x", width=False)
    assert repr(Txt("x")) == "TextDoc(text='x', width=True)"
