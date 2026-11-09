# Install

Cambium needs Python 3.12, 3.13 or 3.14.

```
pip install pycambium
```

The package on PyPI is called `pycambium`, because the name `cambium` was already taken. You import it as `cambium`, and the command is `cambium`:

```
cambium --version
python -c "import cambium; print(cambium.__version__)"
```

Both print `0.9.0`.

## From a source checkout

The tests, the research tools and the reports live in the repository, not in the package:

```
git clone https://github.com/rar-file/cambium
cd cambium
pip install -e ".[test]"
python -m pytest -m "not slow"     # the quick tests; drop -m "not slow" for all of them
```
 A checkout also has the research command, `python cli.py`. It grows the same tree for the same seed; see [Grow a tree](grow.md#the-research-command).

## Bit-identical results

A seed always gives the same tree on the same machine. To come as close as possible to the published runs, match the environment too:

1. Use Python 3.14.7.
2. In a source checkout, install the pinned versions of every library, then Cambium:

```
pip install -r requirements.lock
pip install -e .
```

## One maths thread, on purpose

Cambium runs its maths libraries on one thread. The libraries give slightly different results with different thread counts (measured: up to 0.03 % at age 60). With one thread, a run gives the same bits every time, whatever the number of cores. It costs about 6 % in speed.

Different processors can still differ in the last bits, because the maths library picks its kernel for the processor. Compare runs made on one machine.

You don't have to set anything: importing `cambium` sets the thread count before the libraries load. To use more cores, run several seeds in separate processes.

## Memory and time

- A test run of 10 to 25 years takes seconds to a minute.
- A 60-year open-grown birch has well over a million leaves. It takes several minutes and a few GB of memory.
- A tree grown in a stand is much smaller, so it is faster and needs less memory.
