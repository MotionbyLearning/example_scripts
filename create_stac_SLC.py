from pystac_client import Client
from pystac import Catalog
import glob
import os
import datetime


### This script is to retrieve json files for Sentienl-1 SLCs and create a STAC catalog.
### It should be run in a data stack directory, e.g., '/project/caroline/Data/radar_data/sentinel1/s1_asc_t015/IW_SLC__1SDV_VVVH' on Spider server.


STAC_API_URL = 'https://cmr.earthdata.nasa.gov/stac/ASF'
client = Client.open(STAC_API_URL)



# get all items matching the query
# input: slcs: a list of SLCs, i.e., the 'id' in the json file
# output: items matching the query

def get_items(slcs):

    # get items according to the given SLC list
    search = client.search(    
        ids = slcs
    )    
    items = search.get_all_items()

    # if there are not enough items for the given SLC list
    if len(items) < len(slcs):
        new_slcs=[]
        for slc in slcs:
            search = client.search(    
                ids = slc
            )    
            items = search.get_all_items()
            
            # find which SLC missed the item
            if len(items) == 0:
                print('The json file can not be retrieved: %s.zip'%slc[:-4], file = log)
            
            # create a new SLC list, for each SLC in the list, there is a corresponding item
            else:
                # print('The json file has been retrieved: %s.zip'%slc[:-4])
                new_slcs.append(slc)

        # get items according to the new SLC list
        search = client.search(    
            ids = new_slcs
            )    
        items = search.get_all_items()

    return items




# get the absolute path of the working directory
working_dir = os.path.abspath('.')

# create a log file
log = open('catalog.log', mode = 'w')
time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
print(time, file = log)


# make a loop to get items for every date directory
items_all = []
dates = glob.glob('20*')
dates.sort()
for date in dates:
    print('Retrieve items : %s'%date)
    os.chdir(date)
    
    # prepare a list of SLCs, i.e., the 'id' in the json file
    slcs = []
    zips = glob.glob('*.zip')
    for zip in zips:
        slc = zip[:-4] + '-SLC'
        slcs.append(slc)

    items = get_items(slcs)

    # get a item list which has items of every date directory
    items_all.append(items)

    os.chdir('..')


print('All available json files have been retrieved.', file = log)


# build a catalog for the given items
# N.B.: catalog_type can be 'SELF_CONTAINED', 'RELATIVE_PUBLISHED' or 'ABSOLUTE_PUBLISHED'
catalog = Catalog(
    id = 'SLC-catalog',
    description = 'A catalog for Sentinel-1 SLCs'
    )


# add items to the catalog
for items in items_all:
    catalog.add_items(items)
        
# set hrefs in the default mode
catalog.normalize_hrefs('.')

# change the self_href for every item (i.e., put the retrieved json files in the directory of zip files)
for items in items_all:
    for item in items:
        self_link = item.get_single_link('self')
        if self_link:
            print('Add the item to the catalog : %s'%os.path.split(self_link.target)[1])
            item.set_self_href(os.path.join(working_dir, os.path.split(self_link.target)[1][17:25], os.path.split(self_link.target)[1]))


# save the catalog
catalog.save(catalog_type = 'SELF_CONTAINED')

print('A STAC catalog has been created.', file = log)