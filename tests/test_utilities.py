import pytest
import wadler_lindig as wl


def test_array_summary():
    out = wl.array_summary((2, 3, 4), "float32", None)
    assert out == wl.TextDoc("f32[2,3,4]")
    out = wl.array_summary((2, 3, 4), "float32", "foo")
    assert out == wl.TextDoc("f32[2,3,4](foo)")


@pytest.mark.parametrize("sep", (wl.TextDoc("sep"), wl.BreakDoc("sep")))
def test_bracketed(sep):
    doc = wl.bracketed(
        begin=wl.TextDoc("L"),
        docs=[wl.TextDoc("foo"), wl.TextDoc("bar"), wl.TextDoc("baz")],
        sep=sep,
        end=wl.TextDoc("R"),
        indent=1,
    )
    out = wl.pformat(doc)
    assert out == "LfoosepbarsepbazR"
    out = wl.pformat(doc, width=1)
    if isinstance(sep, wl.BreakDoc):
        assert out == "L\n foo\n bar\n baz\nR"
    else:
        assert out == "L\n foosepbarsepbaz\nR"


def test_join():
    sep = wl.TextDoc("foo")
    objs = [wl.TextDoc("bar"), wl.TextDoc("baz"), wl.TextDoc("qux")]
    out = wl.join(sep, objs)
    assert out == wl.ConcatDoc(
        wl.TextDoc("bar"),
        wl.TextDoc("foo"),
        wl.TextDoc("baz"),
        wl.TextDoc("foo"),
        wl.TextDoc("qux"),
    )


def test_named_objs():
    pairs = [("key", [1, 2, 3])]
    [obj] = wl.named_objs(pairs, indent=1)
    out = wl.pformat(obj)
    assert out == "key=[1, 2, 3]"
    out = wl.pformat(obj, width=1)
    assert out == "key=[\n 1,\n 2,\n 3\n]"
