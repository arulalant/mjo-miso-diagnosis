import os, sys, subprocess, datetime
import cdms2, cdutil
sys.path.append('..')
from auto.cdscan_update import updateCdmlFile
from utils.timeutils import TimeUtility
# global path variables
from config.globalpaths import fcstanopath, mjoAnaInpath, mjoDFcstInpath
cdms2.setAutoBounds('on')
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

checkpastdays = 1

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180317'

tobj = TimeUtility()


def createDeterministicFcstMJOinFiles(curday):
    # os.chdir(anaanopath)
    merged_ana_10daysfcst_anofile = 'um_ana_tseries_and_determisitic_10days_fcst_%s_ano.xml' % curday
    merged_ana_10daysfcst_anofpath = os.path.join(fcstanopath, merged_ana_10daysfcst_anofile)
    inf = cdms2.open(merged_ana_10daysfcst_anofpath)
    cday = tobj.timestr2comp(curday)

    outfile_dfcst = 'um_determisitic_10days_fcst_mjo_project_input_%s.nc' % curday
    outfile_dpath = os.path.join(mjoDFcstInpath, outfile_dfcst)
    outf_df = cdms2.open(outfile_dpath, 'w')

    outfile_ana = 'um_analysis_mjo_project_input_%s.nc' % curday
    outfile_apath = os.path.join(mjoAnaInpath, outfile_ana)
    outf_a = cdms2.open(outfile_apath, 'w')
    for (ivar, lev, longitudunal_norm_factor, ovar) in [
        ('ulwrf', None, 15.1, 'olr'),
        ('u', 20000, 4.81, 'u200'),
        ('u', 85000, 1.81, 'u850'),
    ]:
        for i in range(0, 11, 1):  # 0 will bring past 120 days analysis and 1 to 10 will bring 10 days forecast
            nextday = tobj.moveTime(cday.year, cday.month, cday.day, i)
            previous120day = tobj.moveTime(nextday.year, nextday.month, nextday.day,
                                           -119)  # here -119 will bring previous120day
            previous120data = inf(ivar, time=(previous120day, nextday), level=lev)
            print "previous120data", i, previous120day, nextday, previous120data.shape
            previous120data_mean = cdutil.averager(previous120data, axis='t')
            if i:  # forecast individual 10 days in loop
                nextdaydata = inf(ivar, time=nextday, level=lev)
                axlist = nextdaydata.getAxisList()
                nextdaydata -= previous120data_mean  # subtract previous 120 days (119 days analysis + 1st day fcst)
            else:  # past 120 days analysis
                axlist = previous120data.getAxisList()
                nextdaydata = previous120data - previous120data_mean  # just subtract 120 days mean of analysis
            # end of if i:
            #
            subtropical_data = nextdaydata(latitude=(-15, 15, 'ccb'))
            subtropical_data_avg = cdutil.averager(subtropical_data, axis='y')
            subtropical_data_avg /= longitudunal_norm_factor
            fdata = cdms2.createVariable(subtropical_data_avg, id=ovar)
            axlist = axlist[0:-2] + [axlist[-1]
                                    ]  # i.e omitting latitude axis, since we already averaged over that axis.
            fdata.setAxisList(axlist)
            if i:
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
    while pDay != tDay:  # if we use <= it will run for the actual current day next 10 days fcst.
        # but it will produce xml file with one day gap between till yesterday's analysis and today's next 10days fcst
        # So lets create using (!=) yesterday analysis (all 4 cycles avg) and yesterday's 10days forecast.
        pastDay = pDay.strftime('%Y%m%d')
        outfile = os.path.join(mjoDFcstInpath, 'um_determisitic_10days_fcst_mjo_project_input_%s.nc' % pastDay)
        lag1 = datetime.timedelta(days=1)
        pDay = (pDay + lag1)
        print "outfile", outfile
        nextday = pDay.strftime('%Y%m%d')
        # if not os.path.exists(outfile):
        createDeterministicFcstMJOinFiles(pastDay)
        print "outfile", outfile
        print "Done: ", pastDay
    # end of while pastDay != tDay:
    # end of if __name__ == '__main__':
