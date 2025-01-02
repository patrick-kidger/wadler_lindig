# FAQ

### What is the difference to the built-in `pprint` library?

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

### What is the difference to `black` or `rust format`?

The above are formatters for your source code. This `wadler_lindig` library is intended as an alternative to the built-in `pprint` library, which pretty-format Python objects at runtime.
