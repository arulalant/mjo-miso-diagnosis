import array, os, sys, subprocess
import numpy as np
import cdms2, MV2
cdms2.setAutoBounds('on')
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)
# https://www.johnny-lin.com/cdat_tips/tips_fileio/bin_array.html
dpath = '/gpfs4/home/arulalan/MJO/climatology/Daily/u200'

u200file = cdms2.open(os.path.join(dpath, 'u200.mjo.daily.climatology.1979-2005.nc'))
u200 = u200file('u200')
u200file.close()

binfile = os.path.join(dpath, 'u200.mjo.daily.climatology.1979-2005.bin')
fileobj = open(binfile, mode='wb')
outvalues = array.array('f')
outvalues.fromlist(u200.T.data.flatten('F').tolist())  # make sure access='stream' while reading in fortran
outvalues.tofile(fileobj)
fileobj.close()
subprocess.call('gfortran -c fftpack.F', shell=True)
subprocess.call('gfortran -o calc3har_u200.o calc3har_u200.f fftpack.o', shell=True)
subprocess.call('./calc3har_u200.o', shell=True)

meanfile = os.path.join(dpath, 'u200.clim.mean.1979-2005.bin')
aafile = os.path.join(dpath, 'u200.clim.aa.1979-2005.bin')
bbfile = os.path.join(dpath, 'u200.clim.bb.1979-2005.bin')
num_lon = 144
num_lat = 73
fileobj = open(meanfile, mode='rb')
binvalues = array.array('f')
binvalues.read(fileobj, num_lon * num_lat)
mean = np.array(binvalues).reshape((num_lat, num_lon))
fileobj.close()

fileobj = open(aafile, mode='rb')
binvalues = array.array('f')
binvalues.read(fileobj, 3 * num_lon * num_lat)
aa = np.array(binvalues).reshape((num_lat, num_lon, 3))
fileobj.close()

fileobj = open(bbfile, mode='rb')
binvalues = array.array('f')
binvalues.read(fileobj, 3 * num_lon * num_lat)
bb = np.array(binvalues).reshape((num_lat, num_lon, 3))
fileobj.close()


def multiplyByTimeDim(x, y):
    data = np.array([])
    for i, val in enumerate(y):
        if i == 0:
            data = x * val
        else:
            data = np.concatenate((data, x * val))
    sh = list(x.shape)
    sh.insert(0, len(y))
    return data.reshape(sh)


tt = np.arange(1, 367, 1) - 1.  # 1 to 366, == 0 to 365

mean = np.ma.masked_invalid(mean)
mean_plus_3har = mean + multiplyByTimeDim(aa[:,:,0], np.cos(2.*np.pi*tt*1./366.)) \
                      + multiplyByTimeDim(bb[:,:,0], np.sin(2.*np.pi*tt*1./366.)) \
                      + multiplyByTimeDim(aa[:,:,1], np.cos(2.*np.pi*tt*2./366.)) \
                      + multiplyByTimeDim(bb[:,:,1], np.sin(2.*np.pi*tt*2./366.)) \
                      + multiplyByTimeDim(aa[:,:,2], np.sin(2.*np.pi*tt*3./366.)) \
                      + multiplyByTimeDim(bb[:,:,2], np.sin(2.*np.pi*tt*3./366.))
mean_plus_3har = np.ma.masked_invalid(mean_plus_3har)

print mean_plus_3har.min(), mean_plus_3har.max()
mean_plus_3har = cdms2.createVariable(mean_plus_3har)
mean_plus_3har.id = 'u200_mean_plus_3harmoic_clim'

taxis = cdms2.createAxis(tt, id='time')
taxis.units = 'days since 4-1-1'
taxis.designateTime()
lataxis = cdms2.createAxis(np.arange(-90, 91, 2.5), id='latitude')
lataxis.designateLatitude()
lonaxis = cdms2.createAxis(np.arange(0, 360, 2.5), id='longitude')
lonaxis.designateLongitude()

mean_plus_3har.setAxisList([taxis, lataxis, lonaxis])

outfname = os.path.join(dpath, 'u200.clim.mean+3harm.1979-2005.nc')
outf = cdms2.open(outfname, 'w')
outf.write(mean_plus_3har)
outf.close()
