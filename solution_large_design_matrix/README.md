# Handling of large design matrices in network integration

## Files
- Final proposed solution, based on investigation 2: solution_large_design_mat.ipynb 
- Investigation 1: investigation1_dask_array_sparse_mat.ipynb . Dask arrays + Dask sparse matrices. (Not recommended)
- Investigation 2: investigation2_scipy_sparse_mat.ipynb . SciPy sparse matrices + SciPy sparse linear algebra (Optimal)

## The problem

Consider we have a network with `N_points` points (nodes) and `N_arcs` arcs, each point has a wrapped phase time series with the length of `N_time`. By forming arcs, we have differential phases between the points, and we can solve the ambiguities per arc.

Now we want to integrate the arcs ambiguities into point ambiguities. For a point, there can be multiple arcs connected to it, and if we approach a point following different arcs, the ambiguities solutions may conflict. Therefore we need to find an optimal solution to adjust these errors. A very simplified solution is through the following linear model:


```math
y = Ax
```

where:

- `y` is the known arc ambiguity matrices, with the shape `N_arcs` x `N_time`
- `A` is the design matrix, with the shape `N_arcs` x `N_pixels`. `A` represents the relationship between the arcs and the points, with values -1, 1, and 0. Each row of `A` represent to an arc, with 1 marking the target point of that arc, -1 for the source point.
- `x` is the ambuiguity time series of the points need to be solved, with the shape `N_points` x `N_time`.

Based on Least-Squares principle, assuming all `y` are independent and equally weighted, we can estimate `x` as:

```math
x = (A^T A)^{-1} A^T y
```

If we look into this very simple model, `A` is a very large sparse matrix. In this notebook, we can investigate if there is a simple way in python to perform this computation.

