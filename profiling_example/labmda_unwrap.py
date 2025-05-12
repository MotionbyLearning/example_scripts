import numpy as np
import xarray as xr
from depsi.dynamic_estimation import lambda_estimation


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
NUM_POINTS = 100

FILE_PATH = "../../data/stm_amsterdam_173p.zarr"


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


if __name__ == "__main__":
    # Load all to memory
    stm = xr.open_zarr(FILE_PATH).compute()

    # subset the data for debug
    if NUM_POINTS is not None:
        # Select a subset of points for debugging
        stm = stm.isel(space=range(NUM_POINTS))

    # select the reference point
    nmad_init = np.array(stm["nmad_init"])
    ref_pnt_idx = int(np.argmin(nmad_init))
    stm_refpnt = stm.isel(space=ref_pnt_idx)

    # Initiate emty arrays to store results
    x_hat = np.zeros((stm.sizes["space"], 4))
    Q_xhat = np.zeros((4, 4, stm.sizes["space"]))
    y_hats = np.zeros((stm.sizes["space"], stm.sizes["time"]))
    phs_unw_init = np.zeros((stm.sizes["space"], stm.sizes["time"]))

    # Loop over all points and perform phase unwrapping
    for pnt_id in range(stm.sizes["space"]):
        # Select current point
        stm_1pnt = stm.isel(space=pnt_id)

        print(f"{pnt_id}/{stm.sizes['space']}")

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

        # Store results
        x_hat[pnt_id, :] = results[0]
        Q_xhat[:, :, pnt_id] = results[1]
        y_hats[pnt_id, :] = results[2]
        phs_unw_init[pnt_id, :] = results[3]

    # Write x_hat and Q_xhat to npz files, since they so not fit in dimensions of an STM
    np.savez(
        "./x_hat_Q_xhat.npz",
        x_hat=x_hat,
        Q_xhat=Q_xhat,
    )

    # Attach y_hats and phs_unw_init to the STM, then write to zarr
    stm["y_hats"] = (("space", "time"), y_hats)
    stm["phs_unw_init"] = (("space", "time"), phs_unw_init)
    stm.to_zarr(
        "./stm_amsterdam_173p_init_unw.zarr",
        mode="w",
    )
