from joblib import Memory

cachedir = None  # TODO: use a persistent cache?
memory = Memory(cachedir=cachedir, verbose=0)

from ..netcdf_index import get_nc_variable


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
        'Bering': []
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
def annual_scalar(expt, variable):
    darray = get_nc_variable(expt, 'ocean_scalar.nc', variable,
                             time_units='days since 2000-01-01')
    annual_average = darray.resample('A', 'time').load()
    annual_average.attrs['long_name'] = darray.long_name + ' (annual average)'
    annual_average.attrs['units'] = darray.units

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
    tx = get_nc_variable(expt, 'ocean_month.nc', 'tx_trans_int_z',
                         chunks={'yt_ocean': 200},
                         time_units='days since 1900-01-01')
    tx_trans = tx.sel(xu_ocean=-69).sel(yt_ocean=slice(-72, -52))
    if tx_trans.units == 'Sv (10^9 kg/s)':
        transport = tx_trans.sum('yt_ocean').resample('A', 'time')
    else:
        print('WARNING: Changing units for ', expt)
        transport = tx_trans.sum('yt_ocean').resample('A', 'time')*1.0e-9

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
def sea_surface_temperature(expt):
    SST = get_nc_variable(expt, 'ocean.nc', 'temp',
                          time_units='days since 1900-01-01').isel(st_ocean=0)

    # Average over first year. We would prefer to compare with WOA13 long-term average.
    SST0 = SST.sel(time=slice('1900-01-01', '1901-01-01')).mean('time')

    # Average over last 10 time slices - prefer to do this by year.
    SST = SST.isel(time=slice(-10, None)).mean('time')
    SSTdiff = SST - SST0

    return SST, SSTdiff


@memory.cache
def sea_surface_salinity(expt):
    SSS = get_nc_variable(expt, 'ocean.nc', 'salt',
                          time_units='days since 1900-01-01').isel(st_ocean=0)

    # Average over first year. We would prefer to compare with WOA13 long-term average.
    SSS0 = SSS.sel(time=slice('1900-01-01', '1901-01-01')).mean('time')

    # Average over last 10 time slices - prefer to do this by year.
    SSS = SSS.isel(time=slice(-10, None)).mean('time')
    SSSdiff = SSS - SSS0

    return SSS, SSSdiff
