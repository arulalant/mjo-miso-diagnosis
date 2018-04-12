import os, sys, cdms2
import ceof_diag
sys.path.append('../..')
# global path variables
from config.globalpaths import obsFilteredPath

infiles = [
    ('olr', 'olr', os.path.join(obsFilteredPath, 'olr/daily.filt.20-100.lanz.100.19790101_20051231.ctl')),
    ('u200', 'u200', os.path.join(obsFilteredPath, 'u200/daily.filt.20-100.lanz.100.19790101_20051231.ctl')),
    ('u850', 'u850', os.path.join(obsFilteredPath, 'u850/daily.filt.20-100.lanz.100.19790101_20051231.ctl')),
]

obs_outfile = os.path.join(obsFilteredPath, 'obs_olr_u200_u850_combinedEofs_1979-2001.nc')
ceof_diag.genCeofVars(infiles, obs_outfile, eobjf=True, lat=(-15, 15, 'cob'), NEOF=4, season='all', year=(1979, 2001))
