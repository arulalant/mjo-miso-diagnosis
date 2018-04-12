import os, sys, datetime
import cdms2, xmgrace
sys.path.append('../..')
from utils.phase3d.phase3d import mjo_phase3d
# global path variables
from config.globalpaths import mjoAnaProjpath, mjoDFcstProjpath, mjoAnaAmpPhasepath, mjoDFcstAmpPhasepath, mjo_phase_line_plot_path

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180317'

checkpastdays = 1


def makeProjectedPctsPhases3DPlots(curday, pcs1VarName, pcs2VarName, pcs2Sign=-1, **kwarg):
    """

    KWarg:
        exclude : exclude hours. If some hours list has passed then those
              model hours will be omitted. eg : 01 hour.
              Note : it will omit those exclude model hours directory.
              So for the remaining model anl, fcst hours only plotted the
              projected pcts.

    12.08.2013
    """

    x = kwarg.get('x', None)
    if x is None:
        x = xmgrace.init()
        print "x init"
    # end of if x is None:

    anainfile = os.path.join(mjoAnaProjpath, 'um_analysis_mjo_projected_pcts_%s.nc' % curday)
    dfcstinfile = os.path.join(mjoDFcstProjpath, 'um_determisitic_10days_fcst_mjo_projected_pcts_%s.nc' % curday)

    anaoutfile = os.path.join(mjoAnaAmpPhasepath, 'um_analysis_mjo_projected_pcts_1_2_amppha_%s.nc' % curday)
    dfcstoutfile = os.path.join(mjoDFcstAmpPhasepath,
                                'um_determisitic_10days_fcst_mjo_projected_pcts_1_2_amppha_%s.nc' % curday)

    pcsf = cdms2.open(anainfile)
    ampf = cdms2.open(anaoutfile)

    npc1 = pcsf(pcs1VarName)
    npc2 = pcsf(pcs2VarName)

    sdate = npc1.getTime().asComponentTime()[0]
    # get the phase alone for the sdate
    phase = ampf('ampvar', time=sdate, amp_pha=1, squeeze=1)
    phase = int(phase)
    # multiply npc2 with pcs2sign. By default it wil be
    # multiplied with -1
    npc2 = npc2 * pcs2Sign
    if pcs1VarName.startswith('norm'):
        npc1.id = 'Normalized Projected PC1'
    if pcs2VarName.startswith('norm'):
        npc2.id = 'Normalized Projected PC2'

    anl_fcst = ''
    # Jut to make sure the analysis and fcst hours are in same colors
    # while plotting for its partners
    if anl_fcst in ['Analysis']:
        pcolors = ['magenta', 'blue', 'violet', 'orange', 'red', 'green']
    elif anl_fcst in ['Merged']:
        pcolors = ['red', 'magenta', 'blue', 'violet', 'orange', 'green']
    else:
        pcolors = ['magenta', 'blue', 'violet', 'orange', 'red', 'green']
    # end of if anl_fcst in ['Analysis']:

    ptitle = 'Title'
    outfname = 'phase3d_projected_norm_pcts_%s' % curday
    outfpath = os.path.join(mjo_phase_line_plot_path, outfname)
    # plotting
    x = mjo_phase3d(
        npc1,
        npc2,
        sxyphase=phase,
        colors=pcolors,
        pposition1=None,
        plocation='in',
        mintick=4,
        pdirection='anticlock',
        title=ptitle,
        stitle1='stitle1',
        stitle2='date',
        timeorder=None)
    # save plot
    x.ps(outfpath)
    ampf.close()
    pcsf.close()


# end of def makeProjectedPctsPhases3DPlots(...):

if __name__ == '__main__':

    tDay = datetime.datetime.strptime(startdate, "%Y%m%d")
    lag = datetime.timedelta(days=checkpastdays)
    pDay = (tDay - lag)

    while pDay != tDay:
        pastDay = pDay.strftime('%Y%m%d')
        lag1 = datetime.timedelta(days=1)
        pDay = (pDay + lag1)
        nextday = pDay.strftime('%Y%m%d')
        x = xmgrace.init()
        makeProjectedPctsPhases3DPlots(pastDay, 'norm_pcs1', 'norm_pcs2', x=x)
        print "Done: ", pastDay
    # end of while pastDay != tDay:
    # end of if __name__ == '__main__':
