<h1 align="center">A Wadler–Lindig ✨pretty-printer✨ for Python</h1>

This library is for you if you need:

- Something like the built-in `pprint.pprint`, but which consumes less horizontal space. For example in error messages.
- If you have complicated custom types that you'd like to create pretty well-formatted reprs for. For example nested trees of dataclasses / PyTorch modules / etc.

Main features:

- Absolutely tiny implementation (77 lines of code for the main Wadler–Lindig algorithm, 223 more for teaching it how to handle all Python types).
- Simpler than the original algorithm by Wadler & Lindig (removes some dead code).
- Supports multi-line unbroken text strings.
- Supports ANSI escape codes and colours.
- Zero dependencies.

## Installation

```bash
pip install wadler_lindig
```

## Documentation

Available at [https://docs.kidger.site/wadler_lindig](https://docs.kidger.site/wadler_lindig).

## Example

```python
import dataclasses
import numpy as np
import wadler_lindig as wl

@dataclasses.dataclass
class MyDataclass:
    x: list[str]
    y: np.ndarray

obj = MyDataclass(["lorem", "ipsum", "dolor sit amet"], np.zeros((2, 3)))

wl.pprint(obj, width=30, indent=4)
# MyDataclass(
#     x=[
#         'lorem',
#         'ipsum',
#         'dolor sit amet'
#     ],
#     y=f64[2,3](numpy)
# )
```

## API at a glance

For day-to-day pretty-printing objects: `pprint` (to stdout), `pformat` (as a string), `pdiff` (between two objects).

For creating custom pretty-printed representations:

- The core Wadler–Lindig document types: `AbstractDoc`, `BreakDoc`, `ConcatDoc`, `GroupDoc`, `NestDoc`, `TextDoc`.
- `pdoc` will convert any Python object to a Wadler–Lindig document, with the `__pdoc__` method called on custom types if it is available.
- `ansi_format` (to add ANSI colour codes), `ansi_strip` (to remove ANSI codes).
- Several common helpers for creating Wadler–Lindig documents: `array_summary`, `bracketed`, `comma`, `join`, `named_objs`.

## FAQ

<details>
<summary>What is the difference to the built-in `pprint` library?</summary>

1. The main difference is that the Wadler–Lindig algorithm produces output like

```
MyDataclass(
  x=SomeNestedClass(
    y=[1, 2, 3]
  )
)
```

In contrast `pprint` produces output like

```
MyDataclass(x=SomeNestedClass(y=[1,
                                 2,
                                 3]))
```

which consumes a lot more horizontal space.

2. By default we print NumPy arrays / PyTorch tensors / etc. in a concise form e.g. `f32[2,3](numpy)` to denote a NumPy array with shape `(2, 3)` and dtype `float32`. (Set `short_arrays=False` to disable this.)

3. We provide support for customising the pretty-printed representations of your custom types. Typically this is done via:

    ```python
    import wadler_lindig as wl

    class MyAmazingClass:
        def __pdoc__(self, **kwargs) -> wl.AbstractDoc:
            ...  # Create your pretty representation here!

        def __repr__(self):
            # Calls `__pdoc__` and then formats to a particular width.
            return wl.pformat(self, width=80)
    ```

    In addition we support a `wadler_lindig.pprint(..., custom=...)` argument, if you don't own the type and so cannot add a `__pdoc__` method.

</details>

<details>
<summary>What is the difference to `black` or `rust format`?</summary>

The above are formatters for your source code. This `wadler_lindig` library is intended as an alternative to the built-in `pprint` library, which pretty-format Python objects at runtime.
</details>
