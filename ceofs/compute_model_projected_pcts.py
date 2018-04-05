import os, sys, cdms2, datetime, pickle
import ceof_diag
sys.path.append('..')
# global path variables
from config.globalpaths import obsFilteredPath, mjoAnaInpath, mjoAnaProjpath, mjoDFcstInpath, mjoDFcstProjpath

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180317'

checkpastdays = 1


def makeModelProjectedPCTS(curday):

    anainfile = os.path.join(mjoAnaInpath, 'um_analysis_mjo_project_input_%s.nc' % curday)
    anaoutfile = os.path.join(mjoAnaProjpath, 'um_analysis_mjo_projected_pcts_%s.nc' % curday)

    dfcstinfile = os.path.join(mjoDFcstInpath, 'um_determisitic_10days_fcst_mjo_project_input_%s.nc' % curday)
    dfcstoutfile = os.path.join(mjoDFcstProjpath, 'um_determisitic_10days_fcst_mjo_projected_pcts_%s.nc' % curday)

    obs_outfile = os.path.join(obsFilteredPath, 'obs_olr_u200_u850_combinedEofs_1979-2005.nc')
    f = cdms2.open(obs_outfile)
    obs_pcts_std = [f('pcs_std_%d' % i) for i in range(1, 5)]
    obs_vars_std = {v: f('std_%s_all' % v) for v in ('olr', 'u200', 'u850')}
    f.close()

    eofobjfilepath = os.path.join(obsFilteredPath, 'obs_eofobj_level2_ceof_olr_u200_u850_all_1979-2005.pkl')
    objf = open(eofobjfilepath, 'rb')
    eofobj = pickle.load(objf)
    objf.close()

    ceof_diag.genProjectedPcts(
        anainfile,
        anaoutfile,
        eofobj,
        lat=(-15, 15, 'cob'),
        NEOF=4,
        season='all',
        obs_vars_std=obs_vars_std,
        obs_pcts_std=obs_pcts_std,)

    ceof_diag.genProjectedPcts(
        dfcstinfile,
        dfcstoutfile,
        eofobj,
        lat=(-15, 15, 'cob'),
        NEOF=4,
        season='all',
        obs_vars_std=obs_vars_std,
        obs_pcts_std=obs_pcts_std,)


if __name__ == '__main__':

    tDay = datetime.datetime.strptime(startdate, "%Y%m%d")
    lag = datetime.timedelta(days=checkpastdays)
    pDay = (tDay - lag)

    while pDay != tDay:
        pastDay = pDay.strftime('%Y%m%d')
        outfile = os.path.join(mjoDFcstProjpath, 'um_determisitic_10days_fcst_mjo_projected_pcts_%s.nc' % pastDay)
        lag1 = datetime.timedelta(days=1)
        pDay = (pDay + lag1)
        nextday = pDay.strftime('%Y%m%d')
        if not os.path.exists(outfile): makeModelProjectedPCTS(pastDay)
        print "Done: ", pastDay
    # end of while pastDay != tDay:
    # end of if __name__ == '__main__':
