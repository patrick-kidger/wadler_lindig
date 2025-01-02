import wadler_lindig as wl


def test_pdiff():
    x = "foo\nbar\nbaz"
    y = "foo\nquux\nbaz"
    out = wl.pdiff(x, y)
    assert out == "  foo\n- bar\n+ quux\n  baz"
