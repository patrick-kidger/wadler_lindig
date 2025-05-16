# API

## Pretty printing

The main two functions are [`wadler_lindig.pprint`][] and [`wadler_lindig.pformat`][], to pretty-print (to stdout) or pretty-format (return a string) any Python object.

::: wadler_lindig.pprint

::: wadler_lindig.pformat

The lower-level function [`wadler_lindig.pformat_doc`][] is used to format a Wadler–Lindig document. This is the function that is called by `pprint` and `pformat`.

::: wadler_lindig.pformat_doc

## Pretty diffs

As a utility we offer [`wadler_lindig.pdiff`][] as a quick way to diff two strings. This is a thin wrapper around the Python built-in library `difflib`.

::: wadler_lindig.pdiff

## Colours and ANSI escape codes

As a utility we offer some support for adding colours via ANSI escape codes, or to remove all ANSI escape codes from a string.

::: wadler_lindig.ansi_format

::: wadler_lindig.ansi_strip

## Wadler–Lindig documents

::: wadler_lindig.AbstractDoc
    options:
        members:
            - __add__
            - group
            - nest

::: wadler_lindig.BreakDoc
    options:
        members:
            - __init__

::: wadler_lindig.ConcatDoc
    options:
        members:
            - __init__

::: wadler_lindig.GroupDoc
    options:
        members:
            - __init__

::: wadler_lindig.NestDoc
    options:
        members:
            - __init__

::: wadler_lindig.TextDoc
    options:
        members:
            - __init__

::: wadler_lindig.pdoc

## Utilities

::: wadler_lindig.array_summary

::: wadler_lindig.bracketed

::: wadler_lindig.comma

::: wadler_lindig.join

::: wadler_lindig.named_objs