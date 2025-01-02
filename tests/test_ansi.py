import pytest
import wadler_lindig as wl


def test_ansi():
    x = wl.ansi_format("foo", fg_colour="red", bold=True)
    assert x == "\x1b[1m\x1b[31mfoo\x1b[0m"
    x = wl.ansi_format("foo", fg_colour="red", bold=False)
    assert x == "\x1b[31mfoo\x1b[0m"

    with pytest.raises(ValueError, match="Colour not recognised"):
        wl.ansi_format("foo", fg_colour="foo", bold=False)

    assert wl.ansi_strip(x) == "foo"
