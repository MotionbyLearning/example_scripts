# Profiling example for Network unwrapping

This is an example of how to perform profiling on the Arc Unwrapping algorithms. In this example we used the so-called "LAMBDA method" developed by TUDelft, and use a wrapper function in DePSI to call the unwrapping algorithm.

- LAMBDA method: [LAMBDA.py](https://github.com/TUDelftGeodesy/DePSI_group/blob/dev/depsi/LAMBDA.py) (private repo)
- Wrapper funtion `lambda_estimation`: [lambda_estimation](https://github.com/TUDelftGeodesy/DePSI_group/blob/dev/depsi/LAMBDA.py) (private repo)
- Data needed for the example: [stm_amsterdam_173p.zarr](https://zenodo.org/records/15324181/files/stm_amsterdam_173p.zarr.zip?download=1)


## File structure

- labmda_unwrap.ipynb: Jupyter notebook for debugging and vislualization
- labmda_unwrap.py: Python script for running the unwrapping algorithm in a recursive loop

## Profiling the unwrapping algorithm

We use the `py-spy` package to profile the unwrapping algorithm. For example, we can use the following command to profile the unwrapping algorithm without dask

```python
py-spy record -o profile.svg -- python labmda_unwrap.py
```