import os, sys, datetime
sys.path.append('../..')
from utils.phase3d.amplitude_phase import genMjoAmplitudePhases
# global path variables
from config.globalpaths import mjoAnaProjpath, mjoDFcstProjpath, mjoAnaAmpPhasepath, mjoDFcstAmpPhasepath

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180317'

checkpastdays = 1


def makeModelProjectedPCTS_AmplitutdePhases(curday):

    anainfile = os.path.join(mjoAnaProjpath, 'um_analysis_mjo_projected_pcts_%s.nc' % curday)
    dfcstinfile = os.path.join(mjoDFcstProjpath, 'um_determisitic_10days_fcst_mjo_projected_pcts_%s.nc' % curday)

    anaoutfile = os.path.join(mjoAnaAmpPhasepath, 'um_analysis_mjo_projected_pcts_1_2_amppha_%s.nc' % curday)
    dfcstoutfile = os.path.join(mjoDFcstAmpPhasepath,
                                'um_determisitic_10days_fcst_mjo_projected_pcts_1_2_amppha_%s.nc' % curday)

    genMjoAmplitudePhases(
        infile=anainfile, outfile=anaoutfile, pcs1VarName='norm_pcs1', pcs2VarName='norm_pcs2', pcs2Sign=-1)

    genMjoAmplitudePhases(
        infile=dfcstinfile, outfile=dfcstoutfile, pcs1VarName='norm_pcs1', pcs2VarName='norm_pcs2', pcs2Sign=-1)


if __name__ == '__main__':

    tDay = datetime.datetime.strptime(startdate, "%Y%m%d")
    lag = datetime.timedelta(days=checkpastdays)
    pDay = (tDay - lag)

    while pDay != tDay:
        pastDay = pDay.strftime('%Y%m%d')
        outfile = os.path.join(mjoDFcstAmpPhasepath,
                               'um_determisitic_10days_fcst_mjo_projected_pcts_1_2_amppha_%s.nc' % pastDay)
        lag1 = datetime.timedelta(days=1)
        pDay = (pDay + lag1)
        nextday = pDay.strftime('%Y%m%d')
        # if not os.path.exists(outfile):
        makeModelProjectedPCTS_AmplitutdePhases(pastDay)
        print "Done: ", pastDay
    # end of while pastDay != tDay:
    # end of if __name__ == '__main__':
