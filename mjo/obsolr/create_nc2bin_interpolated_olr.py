import array, os, cdms2

# https://www.johnny-lin.com/cdat_tips/tips_fileio/bin_array.html
dpath = '/gpfs4/home/arulalan/MJO/obs_data/OLR/NCEP-OLR/interpolated'

olrfile = cdms2.open(os.path.join(dpath, 'olr.day.mean.nc'))
olr = olrfile('olr')
olrfile.close()

binfile = os.path.join(dpath, 'olr.total.96toEnd.Binterp.1x.b')
fileobj = open(binfile, mode='wb')
outvalues = array.array('f')
outvalues.fromlist(olr.T.data.flatten('F').tolist())  # make sure access='stream' while reading in fortran
outvalues.tofile(fileobj)
fileobj.close()
