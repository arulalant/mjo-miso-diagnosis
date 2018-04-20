import os, sys, cdms2, datetime, numpy, MV2
sys.path.append('../..')
# global path variables
from config.globalpaths import obsFilteredPath, mjoAnaInpath, mjoAnaProjpath, mjoDFcstInpath, mjoDFcstProjpath

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180317'

checkpastdays = 0
WH04_EOFstruc = 'WH04_Observed_EOFstruc_1979-2001.txt'


def genWH04ProjectedPCTS(infile, outfile, adjustTAxisBy=0):

    # load observed CEOF pattern
    obs_pc1, obs_pc2 = numpy.loadtxt(
        WH04_EOFstruc,
        comments='#',
        delimiter=None,
        usecols=(0, 1),
        unpack=True,)
    # get olr eofs 1 & 2

    # CAUTION : This is the correct order of variables to do ceof.
    # and pcts. ('olr', 'u850', 'u200') is the correct order to do MJO works.
    obs_olr_eof1 = obs_pc1[0:144]
    obs_olr_eof2 = obs_pc2[0:144]
    # get u850 eofs 1 & 2
    obs_u850_eof1 = obs_pc1[144:288]
    obs_u850_eof2 = obs_pc2[144:288]
    # get u200 eofs 1 & 2
    obs_u200_eof1 = obs_pc1[288:432]
    obs_u200_eof2 = obs_pc2[288:432]

    correctOrderVars = [
        ('olr', obs_olr_eof1, obs_olr_eof2),
        ('u850', obs_u850_eof1, obs_u850_eof2),
        ('u200', obs_u200_eof1, obs_u200_eof2),
    ]

    projected_pcts = []
    data_pc1 = 0
    data_pc2 = 0
    f = cdms2.open(infile)
    taxis = f['olr'].getTime()
    newt = taxis[:] + adjustTAxisBy  # required for correction of forecast dates
    newt = cdms2.createAxis(newt, id='time')
    newt.units = taxis.units
    newt.designateTime()

    for (var, eof1, eof2) in correctOrderVars:
        data = f(var, longitude=(0, 357.5, 'ccb'), squeeze=1)
        data_pc1 += MV2.sum(data * eof1, axis=1)
        data_pc2 += MV2.sum(data * eof2, axis=1)
        # make memory free
        del data
    # end of for var in correctOrderVars:
    projected_pc1 = data_pc1 / numpy.sqrt(55.43719)
    projected_pc2 = data_pc2 / numpy.sqrt(52.64146)
    # make projected pcts1 & 2
    projected_pc1 = cdms2.createVariable(projected_pc1, id='RMM1')
    projected_pc1.setAxis(0, newt)
    projected_pc2 = cdms2.createVariable(projected_pc2, id='RMM2')
    projected_pc2.setAxis(0, newt)
    # write output
    f1 = cdms2.open(outfile, 'w')
    f1.write(projected_pc1)
    f1.write(projected_pc2)
    f1.close()
    f.close()


# end of def genProjectedPCTS(infile, outfile):


def makeModelProjectedPCTS(curday):

    anainfile = os.path.join(mjoAnaInpath, 'obsolr_um_analysis_winds_mjo_input_%s.nc' % curday)
    anaoutfile = os.path.join(mjoAnaProjpath, 'obsolr_um_analysis_winds_mjo_projected_pcts_%s.nc' % curday)

    dfcstinfile = os.path.join(mjoDFcstInpath, 'um_determisitic_10days_fcst_mjo_input_%s.nc' % curday)
    dfcstoutfile = os.path.join(mjoDFcstProjpath, 'um_determisitic_10days_fcst_mjo_projected_pcts_%s.nc' % curday)

    genWH04ProjectedPCTS(anainfile, anaoutfile, adjustTAxisBy=0)

    genWH04ProjectedPCTS(dfcstinfile, dfcstoutfile, adjustTAxisBy=-1)


if __name__ == '__main__':

    tDay = datetime.datetime.strptime(startdate, "%Y%m%d")
    lag = datetime.timedelta(days=checkpastdays)
    pDay = (tDay - lag)

    while pDay <= tDay:
        pastDay = pDay.strftime('%Y%m%d')
        outfile = os.path.join(mjoDFcstProjpath, 'um_determisitic_10days_fcst_mjo_projected_pcts_%s.nc' % pastDay)
        lag1 = datetime.timedelta(days=1)
        pDay = (pDay + lag1)
        nextday = pDay.strftime('%Y%m%d')
        # if not os.path.exists(outfile):
        makeModelProjectedPCTS(pastDay)
        print "Done: ", pastDay
    # end of while pastDay != tDay:
    # end of if __name__ == '__main__':
