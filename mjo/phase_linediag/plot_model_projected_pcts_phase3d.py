import os, sys, datetime
import cdms2, xmgrace, MV2
sys.path.append('../..')
from utils.phase3d.phase3d import mjo_phase3d
# global path variables
from config.globalpaths import mjoAnaProjpath, mjoDFcstProjpath, mjoAnaAmpPhasepath, mjoDFcstAmpPhasepath, mjo_phase_line_plot_path

# mjoAnaProjpath = '/Users/arulalan/tmp/mjo'
# mjoDFcstProjpath = '/Users/arulalan/tmp/mjo'
# mjoAnaAmpPhasepath = '/Users/arulalan/tmp/mjo'
# mjoDFcstAmpPhasepath = '/Users/arulalan/tmp/mjo'
# mjo_phase_line_plot_path = '/Users/arulalan/tmp/mjo'

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180405'

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

    pcsf_ana = cdms2.open(anainfile)
    ampf_ana = cdms2.open(anaoutfile)

    pcsf_dfcst = cdms2.open(dfcstinfile)
    ampf_dfcst = cdms2.open(dfcstoutfile)

    npc1_ana = pcsf_ana(pcs1VarName)[-40:]
    npc2_ana = pcsf_ana(pcs2VarName)[-40:]

    npc1_dfcst = pcsf_dfcst(pcs1VarName)
    npc2_dfcst = pcsf_dfcst(pcs2VarName)
    sdate = npc1_ana.getTime().asComponentTime()[0]
    # get the phase alone for the sdate
    phase = ampf_ana('amppha', time=sdate, amp_pha=1, squeeze=1)
    phase = int(phase)
    # multiply npc2 with pcs2sign. By default it wil be
    # multiplied with -1
    npc2_ana = npc2_ana * pcs2Sign
    npc2_dfcst = npc2_dfcst * pcs2Sign

    npc1_ana.id = 'RMM1'
    npc2_ana.id = 'RMM2'

    # npc1_dfcst[0] = npc1_ana[-1]
    # npc2_dfcst[0] = npc2_ana[-1]
    tax = npc1_dfcst.getTime()
    tax_ana = npc1_ana.getTime()[-1]
    newt = tax[:].tolist()
    newt.insert(0, tax_ana)
    ntax = cdms2.createAxis(newt, id='time')
    ntax.units = tax.units
    ntax.designateTime()

    npc1_dfcst = list(npc1_dfcst)
    npc2_dfcst = list(npc2_dfcst)
    npc1_dfcst.insert(0, npc1_ana[-1])  # just make sure that no discontinunity.
    npc2_dfcst.insert(0, npc2_ana[-1])
    npc1_dfcst = cdms2.createVariable(npc1_dfcst, id='RMM1')
    npc2_dfcst = cdms2.createVariable(npc2_dfcst, id='RMM2')
    print len(npc1_dfcst), len(ntax)

    npc1_dfcst.setAxis(0, ntax)
    npc2_dfcst.setAxis(0, ntax)
    pcolors = [6, 8, 3, 2]

    ptitle = 'Title'
    outfname = 'phase3d_projected_norm_pcts_%s' % curday
    outfpath = os.path.join(mjo_phase_line_plot_path, outfname)
    # plotting
    x = mjo_phase3d(
        npc1_ana,
        npc2_ana,
        sxyphase=phase,
        xdata1=npc1_dfcst,
        ydata1=npc2_dfcst,
        dmin=-4,
        dmax=4,
        colors=pcolors,
        pposition1=None,
        plocation='in',
        mintick=4,
        pdirection='anticlock',
        title=ptitle,
        stitle1='date',
        stitle2='date',
        timeorder=None)
    # save plot
    x.pdf(outfpath)
    x.jpeg(outfpath)
    ampf_ana.close()
    pcsf_ana.close()
    pcsf_dfcst.close()


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
