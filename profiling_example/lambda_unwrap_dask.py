import numpy as np
import xarray as xr
import dask
import dask.bag as db
from depsi.dynamic_estimation import lambda_estimation

# Configure dask scheduler
dask.config.set(scheduler="processes") 

# Constants
WAVELENGTH = 0.055465763  # m WAVELENGTH of Sentinel-1 (C-band)

# Initial gauss for the sigma of the unknown parameters
SIGMA_OFFSET = 0.001  # m
SIGMA_VEL = 0.0001  # m/yr
sigma_h = 5  # m
SIGMA_THER = 0.00005  # m/°C

# the option for the LAMBDA METHOD
# METHOD == 1: ILS with shrinking search
# METHOD == 2: Integer rounding
# METHOD == 3: Integer bootstrapping
# METHOD == 4: PAR
# METHOD == 5: ILS with Ratio Test
METHOD = 3

# Number of points to load for debugging
# Set to None to load all points
NUM_POINTS = 60

# Input file path
FILE_PATH = "../../data/stm_amsterdam_173p.zarr"

# Number of partitions for dask bag
# This should be configured because by default dask bag uses ~100 partitions
DB_PATITIONS = 12

def NMAD_to_sigma_phase(nmad, METHOD):
    """
    Converts Normalized Median Absolute Deviation (NMAD) to the sigma of phase observations.

    This function uses an empirical cubic approximation (and is not based on physics):
    sigma = a + b*nmad + c*nmad**2 + d*nmad**3

    Parameters:
    nmad : array_like
        Normalized Median Absolute Deviation value.
    METHOD : {'mean', 'mean_2_sigma'}
        METHOD used to compute sigma.

    Returns:
    sigma: ndarray
        Estimated sigma value.
    """
    if METHOD == "mean":
        a, b, c, d = -0.0144869469, 2.00028682, -5.23271341, 21.1111801
    elif METHOD == "mean_2_sigma":
        a, b, c, d = 0.01907808, 1.2852969, 1.90052824, 11.60677721
    else:
        raise ValueError("Invalid METHOD. Choose 'mean' or 'mean_2_sigma'.")

    sigma = a + b * nmad + c * nmad**2 + d * nmad**3

    return sigma

def lambda_one_point(stm_1pnt, stm_refpnt):
    """
    Estimate the lambda for one point.
    """

    # Get the sigma for the arc with the NMAD from the incremental time series
    sigma_nmad_inc_i = NMAD_to_sigma_phase(
        stm_1pnt["nmad_inc_stm"].data, "mean_2_sigma"
    )
    sigma_nmad_inc_j = NMAD_to_sigma_phase(
        stm_refpnt["nmad_inc_stm"].data, "mean_2_sigma"
    )
    sigma_nmad_inc_arc = np.sqrt(
        np.square(sigma_nmad_inc_i) + np.square(sigma_nmad_inc_j)
    )

    # Compute arc phase
    phs_wrapped_arc = np.angle(
        stm_refpnt["sd_complex"].data * stm_1pnt["sd_complex"].data.conj()
    )

    # Compute 'mean' h2ph value for the arc (which we currently model as the average of the two time series)
    h2ph_arc = (stm_refpnt["h2ph_values"].data + stm_1pnt["h2ph_values"].data) / 2

    results = lambda_estimation(
        wavelength=WAVELENGTH,
        phs_wrapped=phs_wrapped_arc,
        sigma_phs_apri=sigma_nmad_inc_arc,
        years=stm_1pnt["years"].data,
        h2ph_arc=h2ph_arc,
        temp=stm_1pnt["temperature"].data,
        sigma_offset=SIGMA_OFFSET,
        sigma_vel=SIGMA_VEL,
        sigma_h=sigma_h,
        sigma_ther=SIGMA_THER,
        method=METHOD,
    )

    # Unpack results
    x_hat, Q_xhat, y_hat, phs_unw_init = (
        results[0], results[1], results[2], results[3]
    )
    return x_hat, Q_xhat, y_hat, phs_unw_init

if __name__ == "__main__":
    # Load all to memory
    # Must load to memory first since dask bags does not take dask arrays
    # Another option is to load each point by a delayed function before mapping
    stm = xr.open_zarr(FILE_PATH).compute()

    # subset the data for debug
    if NUM_POINTS is not None:
        # Select a subset of points for debugging
        stm = stm.isel(space=range(NUM_POINTS))

    # select the reference point
    nmad_init = np.array(stm["nmad_init"])
    ref_pnt_idx = int(np.argmin(nmad_init))
    stm_refpnt = stm.isel(space=ref_pnt_idx)

    # Initiate empty arrays to store results
    x_hat = np.zeros((stm.sizes["space"], 4))
    Q_xhat = np.zeros((4, 4, stm.sizes["space"]))
    y_hats = np.zeros((stm.sizes["space"], stm.sizes["time"]))
    phs_unw_init = np.zeros((stm.sizes["space"], stm.sizes["time"]))

    stm_bags = db.from_sequence(
        [stm.isel(space=pnt_id) for pnt_id in range(stm.sizes["space"])], npartitions=DB_PATITIONS
    )
    results = stm_bags.map(lambda_one_point, stm_refpnt)
    
    # Compute the results
    results_compute = results.compute()

    # Unpack results
    for pnt_id in range(stm.sizes["space"]):
        x_hat[pnt_id, :], Q_xhat[:, :, pnt_id], y_hats[pnt_id, :], phs_unw_init[pnt_id, :] = results_compute[pnt_id]

    # Write to file
    np.savez(
        "./results.npz",
        x_hat=x_hat,
        Q_xhat=Q_xhat,
        y_hats=y_hats,
        phs_unw_init=phs_unw_init,
    )