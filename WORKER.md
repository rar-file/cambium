# Running the model on a second PC

The second PC's first job is the four golden runs. If its results match this PC's exactly, its results count fully. If they don't, it's used only for exploring, and finalists are confirmed on the main PC.

## On the second PC

1. **Install Python 3.14.7** from python.org. On the first installer screen, tick "Add python.exe to PATH". The version has to be exact.
2. **Copy this project folder across**, from a USB stick or a shared folder. You don't need the `out` folder or the `.venv` folder.
3. **Double-click `run_worker.bat`** in the project folder.
   - The first time, it sets itself up, which needs internet and takes a few minutes.
   - The runs then take about 10-20 minutes, depending on the PC.
   - It needs about 6 GB of free memory, so close big apps first.
4. **When it says "Finished", copy the `worker_out` folder back** to the main PC, for example to `Downloads\worker_out`.

If it stops or the PC restarts, double-click `run_worker.bat` again: finished runs are kept.

## Back on the main PC

Tell the Claude session the folder is there. It runs:

```
python tools/golden.py compare <main PC recording> Downloads/worker_out/hashes.json
```

| Result | What it means |
|---|---|
| IDENTICAL | The second PC's results count fully. |
| DIFFERENT | The second PC is only for exploring. Finalists get confirmed on the main PC. |

The comparison also prints where the two PCs differ: CPU, library versions, thread counts and the OpenBLAS kernel, which is the most likely cause of a difference. It says if the code differs too, which would make the comparison meaningless: copy the folder across again in that case.

## What it won't do

- **It stops if the Python or package versions differ from `requirements.lock`,** because that could change results.
- **It won't launch a run that would leave less than 4 GB of memory free** (PROTOCOL.md section 6). If that happens, close some apps and run it again.
- **It runs cases one at a time,** and only `cli.py` and `tools/plot.py` cases.

## Other jobs

Give it a different case list: `run_worker.bat cases\my_cases.json`. Each case has a name, a rough peak memory in GB, and its command, with `{dir}` for its output folder; `cases\golden.json` is the example.
