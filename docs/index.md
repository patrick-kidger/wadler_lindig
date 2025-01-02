# A Wadler–Lindig ✨pretty-printer✨ for Python

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

## Next steps

Go to the [getting started](./getting_started.ipynb) tutorial for a demonstration of how to create beautiful string representations of all Python types!

## Reference

The main reference for the Wadler–Lindig algorithm is Lindig's paper [available here](https://lindig.github.io/papers/strictly-pretty-2000.pdf).
