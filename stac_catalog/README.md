# STAC catalog example for contextual data

Run this test on Spider: `/project/caroline/Public/demo_mobyle/stac_catalog_contextual/`

## File Structure

`download`: downloaded datasets. Assumed starting point for all scripts. Locate on Spider with the path above.

`data`: location of converted data. This is created in step 1.

`data/catalogs`: STAC catalogs for the converted data. This is created in step 2.

`./environment.yml`: conda environment file for setting up the environment for step 1-3.


## Setup Environment

set up env:

```bash
mamba env create -f environment.yml
```