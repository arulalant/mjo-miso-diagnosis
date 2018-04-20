import os, sys, subprocess, datetime
import cdms2, cdutil
sys.path.append('../..')
from auto.cdscan_update import updateCdmlFile
from utils.timeutils import TimeUtility
# global path variables
from config.globalpaths import fcstanopath, mjoAnaInpath, mjoDFcstInpath
cdms2.setAutoBounds('on')
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

checkpastdays = 0

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180317'

tobj = TimeUtility()


def createDeterministicFcstMJOinFiles(curday):
    # os.chdir(anaanopath)
    merged_ana_10daysfcst_anofile = 'obsolr_um_analysis_tseries-determisitic_10days_fcst_%s_ano.xml' % curday
    merged_ana_10daysfcst_anofpath = os.path.join(fcstanopath, merged_ana_10daysfcst_anofile)
    inf = cdms2.open(merged_ana_10daysfcst_anofpath)
    cday = tobj.timestr2comp(curday)

    outfile_dfcst = 'um_determisitic_10days_fcst_mjo_input_%s.nc' % curday
    outfile_dpath = os.path.join(mjoDFcstInpath, outfile_dfcst)
    outf_df = cdms2.open(outfile_dpath, 'w')

    outfile_ana = 'obsolr_um_analysis_winds_mjo_input_%s.nc' % curday
    outfile_apath = os.path.join(mjoAnaInpath, outfile_ana)
    outf_a = cdms2.open(outfile_apath, 'w')
    for (ivar, lev, longitudunal_norm_factor, ovar) in [
        ('olr', None, 15.11623, 'olr'),  # ncep olr observation
        ('ulwrf', None, 15.11623, 'olr'),  # model analysis+forecast
        ('u', 85000, 1.81355, 'u850'),
        ('u', 20000, 4.80978, 'u200'),
    ]:
        for i in range(-90, 11, 1):
            if i < 0 and ivar == 'ulwrf': continue  # omit ulwrf for past analysis
            if i > 0 and ivar == 'olr': break  # omit olr for forecast
            if i == 0: continue  # skip 0 as needed.
            # just skip 0th -> because in xml file has gap between past obs+analysis and next 10days fcst.
            # -40 to 0 will bring past 120 days observation+analysis and 1 to 10 will bring 10 days forecast
            nextday = tobj.moveTime(cday.year, cday.month, cday.day, i)
            previosNDays = -119 if i < 0 else -120
            previous120day = tobj.moveTime(nextday.year, nextday.month, nextday.day,
                                           previosNDays)  # here -119 will bring previous120day
            previous120data = inf(ivar, time=(previous120day, nextday), level=lev)
            print "previous120data", i, "from", previous120day, "to", nextday, ivar, ovar, previous120data.shape,
            previous120data_mean = cdutil.averager(previous120data, axis='t')
            nextdaydata = inf(ivar, time=nextday, level=lev)
            axlist = nextdaydata.getAxisList()
            nextdaydata -= previous120data_mean  # subtract previous 120 days (119 days analysis + 1st day fcst)

            subtropical_data = nextdaydata(latitude=(-15, 15, 'ccb'))
            subtropical_data_avg = cdutil.averager(subtropical_data, axis='y')
            subtropical_data_avg /= longitudunal_norm_factor
            fdata = cdms2.createVariable(subtropical_data_avg, id=ovar)
            axlist = axlist[0:-2] + [axlist[-1]]
            # i.e omitting latitude axis, since we already averaged over that axis.
            fdata.setAxisList(axlist)
            print fdata.min(), fdata.max()
            if i > 0:
                outf_df.write(fdata)  # forecast file
            else:
                outf_a.write(fdata)  # analysis file
        # end of for i in range(1, 11, 1):
        # end of for (ivar, ....):
    outf_df.close()
    outf_a.close()
    inf.close()


# end of def createAnalysisMJOinFiles(curday):

if __name__ == '__main__':

    tDay = datetime.datetime.strptime(startdate, "%Y%m%d")
    lag = datetime.timedelta(days=checkpastdays)
    pDay = (tDay - lag)
    while pDay <= tDay:  # if we use <= it will run for the actual current day next 10 days fcst.
        # but it will produce xml file with one day gap between till yesterday's analysis and today's next 10days fcst
        # So lets create using (!=) yesterday analysis (all 4 cycles avg) and yesterday's 10days forecast.
        pastDay = pDay.strftime('%Y%m%d')
        outfile = os.path.join(mjoDFcstInpath, 'um_determisitic_10days_fcst_mjo_input_%s.nc' % pastDay)
        lag1 = datetime.timedelta(days=1)
        pDay = (pDay + lag1)
        print "outfile", outfile
        nextday = pDay.strftime('%Y%m%d')
        if not os.path.exists(outfile):
            createDeterministicFcstMJOinFiles(pastDay)
        print "outfile", outfile
        print "Done: ", pastDay
    # end of while pastDay != tDay:
    # end of if __name__ == '__main__':
