# TODO: now use xarray .sel( ... , method='nearest')
#   - note that this isn't needed for slices
#   - how to extract what index was actually used?
# see http://xarray.pydata.org/en/stable/indexing.html#nearest-neighbor-lookups
# and http://xarray.pydata.org/en/stable/generated/xarray.Dataset.sel.html

# TODO: use xarray metadata (data.dims) for dimension names rather than having them hard-coded?

# TODO: handle u,v,t grids carefully for multiple joined transects - depends on B- or C-grid.
#   - are u,v colocated on B grid? doe that mean there's a half-cell extra bit if 2 transects join at 90deg?
# 
# from joblib import Memory
# 
# cachedir = None  # TODO: use a persistent cache?
# memory = Memory(cachedir=cachedir, verbose=0)

from ..netcdf_index import get_nc_variable, get_variables
from ..memory import memory

import logging


# from MOM01_Diagnostics: these are in grid coords
# straights = [ {'name': 'DrakePassage', 'xloc':2100,'ymin':225,'ymax':650},
#               {'name': 'Lombok', 'yloc':1158,'xmin':354,'xmax':361},
#               {'name': 'Ombai', 'xloc':449,'ymin':1152,'ymax':1163},
#               {'name': 'Timor', 'xloc':440,'ymin':1125,'ymax':1145},
#               {'name': 'Bering', 'yloc':2125,'xmin':1080,'xmax':1130},
#               {'name': 'Denmark', 'yloc':2125,'xmin':2380,'xmax':2580},
#             ]

# transects are defined by a tuple of two (lat, lon) tuples,
# i.e. ( (lat, lon) (lat, lon) ), in degrees.
# or a list of such tuples, i.e.
# Either lon or lat must be identical in the two tuples
# to indicate whether it is a meridional or zonal transect.
# i.e. [ ( (lat, lon) (lat, lon) ), ( (lat, lon) (lat, lon) ) ... ].
# lat range = TODO (warning: tripolar for lat>TODO)
# lon range = TODO
# Transects are along grid lines so will not be purely meridional or zonal
# if they extend into tripolar cap region.
transects = \
    {
        'DrakePassage': [],
        'Lombok': [],
        'Ombai': [],
        'Timor': [],
        'Bering': [],
        'Denmark': []
    }
transects['ITF'] = [transects['Lombok'],
                    transects['Ombai'],
                    transects['Timor']]


def nearest_grid(point):
    """
    Find nearest point in horizontal grid.

    Parameters
    ----------
    point : tuple
        Geographic point, either (lat, lon) in degrees
        or (lat, lon, depth) in degrees and meters (negative downward)

    Returns
    -------
    tuple
        Nearest grid indices, either (i, j) or (i, j, k)

    Raises
    ------
    TODO: some sort of range check? or handle this silently?

    """


# @memory.cache
def transport(expt, transect):
    """
    Calculate time series of transport across a transect.

    NB: transport is actually normal to cell boundaries so section is not
    meridional and transport is not purely zonal if `lat` extends into
    tripolar cap region.

    Parameters
    ----------
    expts : str
        Experiment name.
    transect : tuple or list or str
        tuple ( (lat, lon) (lat, lon) ), in degrees.
        or a list of such tuples,
        [ ( (lat, lon) (lat, lon) ), ( (lat, lon) (lat, lon) ) ... ],
        or a key that exists in the `transects` dictionary

    Returns
    -------
    xarray
        Time series of total transport across transect
    """


@memory.cache
def annual_scalar(expt, variables):
    """
    """
    
    logging.debug('Building dataset')
    darray = get_nc_variable(expt,
                             'ocean_scalar.nc',
                             variables,
                             time_units='days since 1700-01-01',
                             use_bag=True,
                             )
    
    logging.debug('Resampling in time')
    annual_average = darray.resample('A', 'time').compute()
    
    for v in annual_average.data_vars:

        avar = annual_average.variables[v]
        dvar = darray.variables[v]
        avar.attrs['long_name'] = dvar.attrs['long_name'] + ' (annual average)'
        avar.attrs['units'] = dvar.attrs['units']

    return annual_average


@memory.cache
def zonal_transport(expt, lon, lat):
    """
    Calculate time series of zonal transport across meridional section.

    NB: transport is actually normal to cell boundaries so section is not
    meridional and transport is not purely zonal if `lat` extends into
    tripolar cap region.

    Parameters
    ----------
    expts : str
        Experiment name.
    lon : float
        Longitude in degrees.
    lat : tuple of two floats
        Starting and ending latitude in degrees.

    Returns
    -------
    xarray
        Time series of zonal transport across meridional section
    """
    tx = get_nc_variable(expt,
                         'ocean_month.nc',
                         'tx_trans_int_z',
                         chunks={'yt_ocean': 200},
                         time_units='days since 1700-01-01',
                         use_bag=False)
    # TODO: check how 'nearest' works with a non-uniform grid!
    # how can it select on xu_ocean when nearest also depends on y?
    tx_trans = tx.sel(xu_ocean=-69, method='nearest')\
        .sel(yt_ocean=slice(-72, -52))
    if tx_trans.units == 'Sv (10^9 kg/s)':
        transport = tx_trans.sum('yt_ocean').resample('A', 'time')
    else:
        print('WARNING: Changing units for ', expt)
        transport = tx_trans.sum('yt_ocean').resample('A', 'time')*1.0e-9

    transport.load()

    return transport


@memory.cache
def drake_passage(expt):
    """
    Calculate time series of zonal transport trough Drake Passage.

    Parameters
    ----------
    expts : str
        Experiment name.

    Returns
    -------
    xarray
        Time series of zonal transport across meridional section
    """
    return zonal_transport(expt, -69, (-72, -52))


@memory.cache
def bering_strait(expt):
    ty = get_nc_variable(expt,'ocean_month.nc',
                         'ty_trans_int_z',
                         chunks={'yu_ocean':200},
                         time_units = 'days since 1700-01-01')
    ty_trans = ty.sel(yu_ocean=67,method='nearest').sel(xt_ocean=slice(-171,-167))
    if ty_trans.units == 'Sv (10^9 kg/s)':
        transport = ty_trans.sum('xt_ocean').resample('A','time')
    else:
        #print('WARNING: Changing units for ', expt)
        transport = ty_trans.sum('xt_ocean').resample('A','time')*1.0e-9

    transport.load()
    
    return transport

@memory.cache
def sea_surface_temperature(expt, resolution=1):
    ## Load SST from expt 
    varlist = get_variables(expt, 'ocean_month.nc')
    if 'surface_temp' in varlist:
        SST = get_nc_variable(expt, 'ocean_month.nc', 'surface_temp',n=10, time_units = 'days since 1700-01-01')
    else:
        SST = get_nc_variable(expt, 'ocean.nc', 'temp',n=10,time_units = 'days since 1700-01-01').isel(st_ocean=0)

    if SST.units == 'degrees K':
        SST = SST - 273.15

    # Annual Average  WOA13 long-term climatology.
    if resolution==1:
        SST_WOA13 = get_nc_variable('woa13/10', 'woa13_ts_\d+_mom10.nc', 'temp').isel(ZT=0)
    elif resolution==0.25:
        SST_WOA13 = get_nc_variable('woa13/025', 'woa13_ts_\d+_mom025.nc', 'temp').isel(ZT=0)
    elif resolution==0.1:
        SST_WOA13 = get_nc_variable('woa13/01', 'woa13_ts_\d+_mom01.nc', 'temp').isel(ZT=0)
    else:
        print('WARNING: Sorry, we dont seem to recognise resolution ', resolution)
    
    # Average
    SST = SST.mean('time')
    SSTdiff = SST - SST_WOA13.mean('time').values

    return SST, SSTdiff


@memory.cache
def sea_surface_salinity(expt, resolution=1):
    ## Load SSS from expt 
    varlist = get_variables(expt, 'ocean_month.nc')
    if 'surface_salt' in varlist:
        SSS = get_nc_variable(expt, 'ocean_month.nc', 'surface_salt',n=10)
    else:
        SSS = get_nc_variable(expt, 'ocean.nc', 'salt',n=10).isel(st_ocean=0)


    # Annual Average  WOA13 long-term climatology.
    if resolution==1:
        SSS_WOA13 = get_nc_variable('woa13/10', 'woa13_ts_\d+_mom10.nc', 'salt').isel(ZT=0)
    elif resolution==0.25:
        SSS_WOA13 = get_nc_variable('woa13/025', 'woa13_ts_\d+_mom025.nc', 'salt').isel(ZT=0)
    elif resolution==0.1:
        SSS_WOA13 = get_nc_variable('woa13/01', 'woa13_ts_\d+_mom01.nc', 'salt').isel(ZT=0)
    else:
        print('WARNING: Sorry, we dont seem to recognise resolution ', resolution)

    # Average over last 10 time slices - prefer to do this by year.
    SSS = SSS.mean('time')
    SSSdiff = SSS - SSS_WOA13.mean('time').values

    return SSS, SSSdiff

@memory.cache
def mixed_layer_depth(expt):
    ## Load MLD from expt 
    varlist = get_variables(expt, 'ocean_month.nc')
    if 'mld' in varlist:
        MLD = get_nc_variable(expt, 'ocean_month.nc', 'mld',n=10)

    # Average over last 10 time slices - prefer to do this by year.
    MLD = MLD.mean('time')

    return MLD
