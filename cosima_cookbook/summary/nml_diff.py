#!/usr/bin/env python3
"""
General-purpose tools to read, superset and diff Fortran namelist files.

Andrew Kiss https://github.com/aekiss
"""

import f90nml  # from http://f90nml.readthedocs.io
import os


def nmldict(nmlfnames):
    """
    Return dict of the groups/group members of multiple Fortran namelist files.

    Parameters
    ----------
    nmlfnames : str, tuple or list
        string, or tuple or list of any number of namelist file path strings.
        Missing, repeated, or non-namelist files are silently ignored.

    Returns
    -------
    dict
        dict with `key`:`value` pairs where
        `key` is filename path string
        `value` is complete Namelist from filename as returned by f90nml.read

    """
    if isinstance(nmlfnames, str):
        nmlfnames = [nmlfnames]
    nmlfnames = set(nmlfnames)  # remove any duplicates from nmlfnames

    nmlall = {}  # dict keys are nml paths, values are Namelist dicts
    for nml in nmlfnames:
        if os.path.exists(nml):
            nmlall[nml] = f90nml.read(nml)
        # TODO: raise error if file not found or not a readable namelist
    return nmlall


def superset(nmlall):
    """
    Return dict of groups/group members present in any of the input Namelists.

    Parameters
    ----------
    nmlall : dict
        dict (e.g. returned by nmldict) with `key`:`value` pairs where
        `key` is arbitrary (typically a filename string)
        `value` is Namelist (typically from filename via f90nml.read)

    Returns
    -------
    dict
        dict with `key`:`value` pairs where
        `key` is group name (including all groups present in any input Namelist)
        `value` is Namelist for group (including every member present in this
            group in any input Namelist)

    """
    nmlsuperset = {}
    for nml in nmlall:
        nmlsuperset.update(nmlall[nml])
    # nmlsuperset now contains all groups that were in any nml
    for group in nmlsuperset:
        # to avoid the next bit changing the original groups
        nmlsuperset[group] = nmlsuperset[group].copy()
        for nml in nmlall:
            if group in nmlall[nml]:
                nmlsuperset[group].update(nmlall[nml][group])
    # nmlsuperset groups now contain all keys that were in any nml
    return nmlsuperset


def nmldiff(nmlall):
    """
    Remove every group/group member that is the same in all file Namelists.

    Parameters
    ----------
    nmlall : dict
        dict (e.g. returned by nmldict) with `key`:`value` pairs where
        `key` is arbitrary (typically a filename path string)
        `value` is Namelist (typically from filename via f90nml.read)

    Returns
    -------
    dict
        Modified input dict with `key`:`value` pairs where
        `key` is arbitrary (typically a filename path string)
        `value` is Namelist from nmlall, with any group/group member
                common to all other keys (i.e. files) in input removed

    """
# Create diff by removing common groups/members from nmlall.
# This is complicated by the fact group names / member names may differ
# or be absent across different nml files.
#
# First make a superset that has all group names and group members that
# appear in any nml file
    nmlsuperset = superset(nmlall)

    # now go through nmlall and remove any groups / members from nmlall that
    #   are identical to superset in all nmls
    # first delete any group members that are common to all nmls, then delete
    #   any empty groups common to all nmls
    for group in nmlsuperset:
        # init: whether group is present and identical in all namelist files
        deletegroup = True
        for nml in nmlall:
            deletegroup = deletegroup and (group in nmlall[nml])
        if deletegroup:  # group present in all namelist files
            for mem in nmlsuperset[group]:
                # init: whether group member is present and identical
                #   in all namelist files
                deletemem = True
                for nml in nmlall:
                    deletemem = deletemem and (mem in nmlall[nml][group])
                if deletemem:  # group member is present in all namelist files
                    for nml in nmlall:
                        # ... now check if values match in all namelist files
                        deletemem = deletemem and \
                            (nmlall[nml][group][mem] ==
                             nmlsuperset[group][mem])
                    if deletemem:
                        for nml in nmlall:
                            # delete mem from this group in all nmls
                            del nmlall[nml][group][mem]
            for nml in nmlall:
                deletegroup = deletegroup and (len(nmlall[nml][group]) == 0)
            if deletegroup:
                # group is common to all nmls and now empty so delete
                for nml in nmlall:
                    del nmlall[nml][group]
    return nmlall


def strnmldict(nmlall, format=''):
    """
    Return string representation of dict of Namelists.

    Parameters
    ----------
    nmlall : dict
        dict (e.g. returned by nmldict) with `key`:`value` pairs where
        `key` is arbitrary (typically a filename path string)
        `value` is Namelist (typically from filename via f90nml.read)

    format : str, optional, case insensitive
        'md' or 'markdown': github Markdown string output
        anything else: standard string output

    Returns
    -------
    string
        String representaion of nmlall.
        Default lists alphabetically by group, member, then dict key,
        with undefined namelist members shown as blank.

    """
    nmldss = superset(nmlall)
    fnames = list(nmlall.keys())
    fnames.sort()
    colwidth = max((len(f) for f in fnames), default=0)
    # TODO: would be faster & more efficient to .append a list of strings
    # and then join them:
    # http://docs.python-guide.org/en/latest/writing/structure/#mutable-and-immutable-types
    st = ''
    if format.lower() in ('md', 'markdown'):
        if len(nmldss) > 0:
            st += '| ' + 'File'.ljust(colwidth) + ' | '
            nmem = 0
            for group in sorted(nmldss):
                for mem in sorted(nmldss[group]):
                    st += '&' + group + '<br>' + mem + ' | '
                    nmem += 1
            st += '\n|-' + '-' * colwidth + ':|' + '--:|' * nmem
            for fn in fnames:
                st += '\n| ' + fn + ' | '
                for group in sorted(nmldss):
                    for mem in sorted(nmldss[group]):
                        if group in nmlall[fn]:
                            if mem in nmlall[fn][group]:
                                st += repr(nmlall[fn][group][mem])
                        st += ' | '
    else:
        for group in sorted(nmldss):
            for mem in sorted(nmldss[group]):
                st += ' ' * (colwidth + 2) + '&{}\n'.format(group)
                st += ' ' * (colwidth + 2) + ' {}\n'.format(mem)
                for fn in fnames:
                    st += '{} : '.format(fn.ljust(colwidth))
                    if group in nmlall[fn]:
                        if mem in nmlall[fn][group]:
                            st += repr(nmlall[fn][group][mem])
                    st += '\n'
    return st


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=
        'Show semantic differences between multiple Fortran namelist files.\
        Differences are listed alphabetically by group, member, then filename.\
        Undefined namelist members are shown as blank.\
        Missing, repeated, or non-namelist files are silently ignored.\
        Exit code 0: no differences; 1: differences.')
    parser.add_argument('file', metavar='file', type=str, nargs='+',
                        help='Fortran namelist file')
    args = parser.parse_args()
    args = vars(args)['file']
    nmld = nmldiff(nmldict(args))
    nmldss = superset(nmld)
    if len(nmldss) == 0:
        sys.exit(0)
    else:
        print(strnmldict(nmld), end='', flush=True)
        sys.exit(1)
