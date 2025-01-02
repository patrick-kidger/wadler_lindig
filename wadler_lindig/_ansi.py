import re


_colour_codes = {
    "black": "\x1b[30m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "blue": "\x1b[34m",
    "magenta": "\x1b[35m",
    "cyan": "\x1b[36m",
    "white": "\x1b[37m",
}


def ansi_format(text: str, fg_colour: str, bold: bool) -> str:
    """Formats `text` with a foreground colour `fg_colour`, and optionally mark it
    `bold`, using ANSI colour codes.
    """
    try:
        colour_code = _colour_codes[fg_colour]
    except KeyError as e:
        raise ValueError(
            f"Colour not recognised. Valid colours are {tuple(_colour_codes.keys())}"
        ) from e
    out = f"{colour_code}{text}\x1b[0m"
    if bold:
        out = "\x1b[1m" + out
    return out


_ansi_regex = re.compile(r"\x1b\[[;?0-9]*[a-zA-Z]")


def ansi_strip(text: str) -> str:
    """Removes all ANSI codes from a string."""
    return _ansi_regex.sub("", text)
