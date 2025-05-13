# Profiling example for Network unwrapping

This is an example of how to perform profiling on the Arc Unwrapping algorithms. In this example we used the so-called "LAMBDA method" developed by TUDelft, and use a wrapper function in DePSI to call the unwrapping algorithm.

- LAMBDA method: [LAMBDA.py](https://github.com/TUDelftGeodesy/DePSI_group/blob/dev/depsi/LAMBDA.py) (private repo)
- Wrapper funtion `lambda_estimation`: [lambda_estimation](https://github.com/TUDelftGeodesy/DePSI_group/blob/dev/depsi/LAMBDA.py) (private repo)
- Data needed for the example: [stm_amsterdam_173p.zarr](https://zenodo.org/records/15324181/files/stm_amsterdam_173p.zarr.zip?download=1)


## File structure

- labmda_unwrap.ipynb: Jupyter notebook for debugging and vislualization
- labmda_unwrap.py: Python script for running the unwrapping algorithm in a recursive loop
- labmda_unwrap_dask.ipynb: Jupyter notebook for debugging dask method
- labmda_unwrap_dask.py: Python script for running the same unwrapping algorithm with dask databags

## Profiling the unwrapping algorithm

We use the `py-spy` package to profile the unwrapping algorithm. For example, we can use the following command to profile the unwrapping algorithm without dask

### Loop method

```sh
py-spy record --output profile_loop_60pnts --idle --rate 5 --subprocesses --format speedscope python labmda_unwrap.py
```

### Dask with `processes` schedular:

In `labmda_unwrap_dask.py` configure: 

```py
# Configure dask scheduler
dask.config.set(scheduler="processes") 
```

```sh
py-spy record --output profile_dask_60pnts_processes --idle --rate 5 --subprocesses --format speedscope python labmda_unwrap_dask.py
```

### Dask with `threads` schedular:

```py
# Configure dask scheduler
dask.config.set(scheduler="threads") 
```

```sh
py-spy record --output profile_dask_60pnts_threads --idle --rate 5 --subprocesses --format speedscope python labmda_unwrap_dask.py
```

Then you can visualize the profile using the [`speedscope` web tool](https://www.speedscope.app/)