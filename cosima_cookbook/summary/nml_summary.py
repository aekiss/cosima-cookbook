#!/usr/bin/env python
"""
Tools to display Fortran namelist dfference between run directories.

Andrew Kiss https://github.com/aekiss
"""

# Create tabulated summary of namelists for a set of files.
# These functions assume we are dealing with ACCESS-OM2 data.
# Andrew Kiss https://github.com/aekiss


# import cosima_cookbook as cc
# from nml_diff import nmldiff, nmldict, superset, strnmldict
from .nml_diff import nmldiff, nmldict, superset, strnmldict
# from IPython.display import display, Markdown
import IPython.display
import os


def nmldiff_md(files):
    IPython.display.display(IPython.display.Markdown(
        strnmldict(nmldiff(nmldict(files)), format='md')))
    return


def summary_md(configuration, expts, path='/g/data3/hh5/tmp/cosima/',
               search='https://github.com/OceansAus/access-om2/search?&q=',
               nmls=[
        'atmosphere/input_atm.nml',
        'ice/cice_in.nml',
        'ice/input_ice.nml',
        'ice/input_ice_gfdl.nml',
        'ice/input_ice_monin.nml',
        'ocean/input.nml'
                   ]):
    for nml in nmls:
        epaths = []
        for e in expts:
            # NB: only look at output000
            epaths.append(os.path.join(path, configuration,
                                       e, 'output000', nml))
        nmld = nmldiff(nmldict(epaths))
        # epaths = list(nmld.keys())  # redefine to handle missing paths
        # epaths.sort()
        nmldss = superset(nmld)
        # display(Markdown('### ' + nml + ' namelist differences'))
        # if len(nmldss) == 0:
        #     display(Markdown('no differences'))
        # else:
        if len(nmldss) > 0:
            IPython.display.display(IPython.display.Markdown(
                '### ' + nml + ' namelist differences'))
            IPython.display.display(IPython.display.Markdown(
                strnmldict(nmld, format='markdown')))
#             display(Markdown('no differences'))
#             mdstr = '| group | variable | '
#             for e in epaths:
#                 mdstr = mdstr + e.replace('/', '/<br>') + ' | '
#             mdstr = mdstr + '\n|---|:--|' + ':-:|' * len(epaths)
#             for group in sorted(nmldss):
#                 for mem in sorted(nmldss[group]):
#                     mdstr = mdstr + '\n| ' + '&' + \
#                             group + ' | ' + \
#                             mem + ' | '
# #                        search doesn't work on github submodules or forks
# #                        '[' + group + '](' + search + group + ')' + ' | ' + \
# #                        '[' + mem + '](' + search + mem + ')' + ' | '
#                     for e in epaths:
#                         if group in nmld[e]:
#                             if mem in nmld[e][group]:
#                                 mdstr = mdstr + repr(nmld[e][group][mem])
#                         mdstr = mdstr + ' | '
#             display(Markdown(mdstr))
    return


# TODO: get this CLI bit working
if __name__ == '__main__':
    # from . import summary
    import argparse
    import sys
    # import os
    from pathlib import Path
    parser = argparse.ArgumentParser(description=
        'Show semantic differences between Fortran namelist files in\ COSIMA (http://cosima.org.au) ocean-ice model output directories.\
        Differences are listed alphabetically by group, member, then filename.\
        Undefined namelist members are shown as blank.\
        Missing, repeated, or non-namelist files are silently ignored.\
        Exit code 0: no differences; 1: differences.')
    parser.add_argument('dir', metavar='dir', type=str, nargs='+',
                        help='model run output??? directory path')
    args = parser.parse_args()
    dirs = vars(args)['dir']
    # nmls = [
    #     'atmosphere/input_atm.nml',
    #     'ice/cice_in.nml',
    #     'ice/input_ice.nml',
    #     'ice/input_ice_gfdl.nml',
    #     'ice/input_ice_monin.nml',
    #     'ocean/input.nml'
    #                ])

    # auto-detect all nml files in first dir arg
    # and *assume* the same applies for the other dir args
    nmls = list(Path(args[0]).glob('**/*.nml'))  # warning: may be slow!
    nmls.sort()
    exitcode = 0
    for nml in nmls:
        dpaths = []
        for d in dirs:
            dpaths.append(os.path.join(d, nml))
        nmld = nmldiff(nmldict(dpaths))
        nmldss = superset(nmld)
        if len(nmldss) > 0:
            print(strnmldict(nmld), end='', flush=True)
            exitcode = 1
    sys.exit(exitcode)
