# How the WL algorithm works

Wadler–Lindig pretty printing happens in two steps.

First, we represent the object as a nested collection of _Wadler–Lindig documents_, corresponding to unbroken text, places that newlines can be inserted, etc. This describes the pretty representation, but for which no maximum width has yet been set.

Second, once provided a width, this nested structure of documents is then passed to the _Wadler–Lindig algorithm_, which lays out the text within the space constraints.

There are five kinds of Wadler–Lindig document:

- [`wadler_lindig.BreakDoc`][]: either inserts a newline or the specified text.
- [`wadler_lindig.ConcatDoc`][]: concatenates multiple documents together.
- [`wadler_lindig.GroupDoc`][]: all elements in the group will either be laid out horizontally together, or vertically together.
- [`wadler_lindig.NestDoc`][]: if laying out vertically, then all child `BreakDoc`s will have this much indent added after their newlines.
- [`wadler_lindig.TextDoc`][]: an unbroken string of text.

As such, the `wadler_lindig` library actually does two distinct things:

1. It converts Python objects into Wadler–Lindig documents.
2. It runs the Wadler–Lindig algorithm for formatting Wadler–Lindig documents.

When we run [`wadler_lindig.pprint`][] or [`wadler_lindig.pformat`][], then both of these happen back-to-back.

Now that we know this, we can customise how types are displayed by specifying how to turn custom Python objects into Wadler–Lindig documents. This is the subject of [our next example](custom_pprints.ipynb).