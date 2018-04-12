import cdms2, MV2
cdms2.setAutoBounds('on')
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

outfile = '/gpfs4/home/arulalan/MJO/climatology/Daily/3vars/ulwrf_u200_850_merged.clim.mean+3harm.1979-2001.nc'

olrf = cdms2.open('/gpfs4/home/arulalan/MJO/climatology/Daily/olr/olr.clim.mean+3harm.1979-2001.nc')

u200f = cdms2.open('/gpfs4/home/arulalan/MJO/climatology/Daily/u200/u200.clim.mean+3harm.1979-2001.nc')

u850f = cdms2.open('/gpfs4/home/arulalan/MJO/climatology/Daily/u850/u850.clim.mean+3harm.1979-2001.nc')

outf = cdms2.open(outfile, 'w')
olr = olrf('olr_mean_plus_3harmoic_clim')
olr.id = 'ulwrf'

u200 = u200f('u200_mean_plus_3harmoic_clim')
u850 = u850f('u850_mean_plus_3harmoic_clim')

sh = list(u200.shape)
sh.insert(1, 2)
u = MV2.zeros(sh)
u[:, 0, :, :] = u850[:, :, :]
u[:, 1, :, :] = u200[:, :, :]

axlist1 = u200.getAxisList()
levAxis1 = cdms2.createAxis([85000., 20000.], id='lev')
levAxis1.units = 'Pa'
levAxis1.designateLevel()
axlist1.insert(1, levAxis1)

u = cdms2.createVariable(u, id='u')
u.setAxisList(axlist1)

outf.write(u)
outf.write(olr)

outf.close()

olrf.close()
u200f.close()
u850f.close()
