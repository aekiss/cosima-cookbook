# cosima-cookbook

[![Travis CI Build Status](https://travis-ci.org/OceansAus/cosima-cookbook.svg?branch=master)](https://travis-ci.org/OceansAus/cosima-cookbook)
[![Documentation Status](https://readthedocs.org/projects/cosima-cookbook/badge/?version=latest)](https://cosima-cookbook.readthedocs.org/en/latest)

https://readthedocs.org/projects/mpi4py/badge/?version=latest

The cosima-cookbook a collection of Jupyter notebooks that show analyses
of ocean and sea ice model output. The focus is on the models run by the members of
[COSIMA: Consortium for Ocean-Sea Ice Modelling in Australia](http://cosima.org.au)

Contributions of new notebooks or analysis scripts are welcomed.

See [Getting Started](http://cosima-cookbook.readthedocs.io/en/latest/getting_started.html) for information on
using the cosima-cookbook.

These notebooks are designed to run on [NCI Virtual Desktop Infrastructure (VDI)](http://nci.org.au/services/vdi/).

## Making git play nicely with Jupyter notebooks
The standard git merge and diff tools don't work well with Jupyter notebooks, so it's better to install content-aware merge and diff using [nbdime](https://nbdime.readthedocs.io). On VDI, bring up a terminal (e.g. from Jupyter in your browser) and do
```
pip install --user nbdime
```

This will install nbdime in `~/.local/bin`. If `which nbdime` shows it can't be found, you'll need to add `~/.local/bin` to your path: 
edit `~/.bash_profile` (e.g. via `nano ~/.bash_profile`) and add 
```
PATH=$PATH:$HOME/.local/bin/
export PATH
```
to the end. Save and exit the editor, then `source ~/.bash_profile`.

Now do
```
nbdime config-git --enable --global
```
to set up git to use nbdime for diff and merge.
