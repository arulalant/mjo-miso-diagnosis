import numpy, cdms2, cdutil, genutil, os, sys, pickle
from eofs.multivariate.cdms import MultivariateEof
sys.path.append('../..')
from utils.timeutils import TimeUtility
# global path variables
from config.globalpaths import fcstanopath, mjoAnaInpath, mjoDFcstInpath
cdms2.setAutoBounds('on')
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

timeobj = TimeUtility()


def getZonalNormStd(data):
    """
    data - pass filtered data
    Return : normalized data and std of the meridionally averaged data.
        Once we averaged over latitude, then it will become zonal data.
    """
    # todo : correct the commented, docstr line for meridionally, zonally
    # meridionally averaged data (averaged over latitude axis)
    # weight='weighted' is default option that will generate the area weights
    meridional_avg = cdutil.averager(data, axis='y')(squeeze=1)  #, weight='weighted')
    # make memory free
    del data
    # averaged over time axis
    time_avg = cdutil.averager(meridional_avg, axis='t', weight='equal')(squeeze=1)
    # get the std
    std_avg = numpy.sqrt(meridional_avg.asma().var())
    # get the normalize the data
    normal_data = (meridional_avg - time_avg) / std_avg
    # make memory free
    del meridional_avg, time_avg
    # return normal_data and std_avg data
    return normal_data, std_avg


# end of def getZonalNormStd(data):


def genCeofVars(infiles, outfile, eobjf=True, lat=(-15, 15, 'cob'), NEOF=4, season='all', **kwarg):
    """
    genCeofVars : generate the combined eof variables as listed below.

    Input :-

    infiles : List of tuples contains variable generic name, actual varible
              name (say model varName), data path. So ceof input files list
              contains the tuples which contains the above three information.

              For eg : ceof(olr, u200, u850)
              infiles = [('olr', 'olrv', 'olr.ctl'),
                         ('u200', 'u200v', 'u200.ctl'),
                         ('u850', 'u850v', 'u850.ctl')]

    outfile : output nc file path. All the supported output varibles of ceof
              will be stored in this nc file. This nc file will be opened in
              append mode.

    eobjf : eof obj file store. If True, the eofobj of ceof will be stored
            as binary ('*.pkl') file in the outfile path directory,
            using pickle module.

    lat : latitude to extract the data of the input file.
          By default it takes as (-15, 15, 'cob').

    NEOF : no of eof or no of mode. By default it takes 4.

    season : It could be 'all', 'sum', 'win'. Not a list.
         all : through out the year data from all the available years
         sum : only summer data will be extracted from all the available years
         win : only winter data will be extracted from all the available years

    Output : The follwing output varibles from 1 to 5 will be stored/append
             into outfile along with individual varName, season
             (where ever needed).
        1. Std of each zonal normalized varibles
        2. Percentage explained by ceof input variables
        3. variance accounted for ceof of each input variables
        4. eof variable of each input variables
        5. PC time series, Normalized PC time Series (for 'all' season only)
        6. Store the eofobj (into .pkl file) [optional]

    Written By : Dileep.K, Arulalan.T

    Date :

    Updated : 11.05.2013

    """

    eofobj_endname = kwarg.get('eofobj_endname', None)
    year = kwarg.get('year', None)
    vnames = []
    variableNames = []
    normals = []
    variances = []
    out = cdms2.open(outfile, 'w')

    for name, varName, infile in infiles:
        print "Collecting data %s for season %s" % (name, season)
        if season == 'all':
            f = cdms2.open(infile)
            if year:
                period = timeobj._getYearFirstLast(year)
                data = f(varName, time=period, latitude=lat, squeeze=1)
            else:
                data = f(varName, latitude=lat, squeeze=1)
            # end of if year:
            f.close()
        elif season == 'sum':
            data = timeobj.getSummerData(varName, infile, latitude=lat, **kwarg)
        elif season == 'win':
            data = timeobj.getWinterData(varName, infile, latitude=lat, **kwarg)
        else:
            raise ValueError("arg 'season' must be either 'all/sum/win' only")
        # end of if season == 'all':
        print "Calculating Zonal Normalized data & its Std, variance"
        # get the normalized data & std of meridionally averaged data
        normal, std = getZonalNormStd(data)
        # make memory free
        del data

        # append the normalize data into normals list
        normals.append(normal)
        # append the variance data into variances list
        variance = normal.asma().var()
        variances.append(variance)

        # set std meta data attributes
        std = cdms2.createVariable(std)
        std.id = '_'.join(['std', name, season])
        std.comments = ''
        out.write(std)

        # store the input variable generic name
        vnames.append(name)
        variableNames.append(name)
        # make memory free
        del normal, std, variance
    # end of for name, varName, infile in infiles:

    print "Calculating multiple eof"
    # get the eofobj by passing multiple normalized varibles of meridionally
    # averaged data. eg(norm_olr, norm_u200, norm_850)
    eofobj = MultivariateEof(normals)

    if eobjf:
        variableNames.sort()
        # generate the eofobj binary file name and its path
        path = os.path.dirname(outfile)
        syear = '%d-%d' % year if year else ''
        eofobj_filename = ['obs_eofobj', 'level2', 'ceof'] + variableNames + [season, syear]
        eofobj_filename = '_'.join(eofobj_filename)
        if eofobj_endname: eofobj_filename += '_' + eofobj_endname
        eofobj_filename += '.pkl'
        eofobj_fpath = os.path.join(path, eofobj_filename)
        # store the eofobj into binary file using pickle module
        objf = open(eofobj_fpath, 'wb')
        pickle.dump(eofobj, objf, 2)
        comment = ''
        pickle.dump(comment, objf, 2)
        objf.close()
        print "Saved the ceof object into file", eofobj_fpath
    # end of if eobjf:

    # generate the eof for each input variables
    eof_vars = eofobj.eofs(neofs=NEOF, eofscaling=2)

    for eof_var, name in zip(eof_vars, vnames):
        # set eof variable name with season and write into nc file
        eof_var.id = '_'.join(['eof', name, season])
        eof_var.comments = ''
        out.write(eof_var)
    # end of for eof_var in zip(eof_vars, vnames):

    # make memory free
    del eof_vars

    # Percentage explained by ceof input variables
    per_exp = eofobj.varianceFraction(neigs=NEOF) * 100
    per_exp.id = '_'.join(['per_exp', 'ceof', season])
    per_exp.comments = ''
    out.write(per_exp)

    # make memory free
    del per_exp

    # construct variable for no of input varibles and NEOF
    cvar = numpy.zeros((len(variances), NEOF))
    for i in range(NEOF):
        reCFileds = eofobj.reconstructedField(i + 1)
        j = 0
        for reCField, variance in zip(reCFileds, variances):
            cvar[j][i] = reCField.asma().var() / variance
            j += 1
        # end of for reCField, var in reCFileds, variances:
        # end of for i in range(NEOF):

        # variance axis start from 1 (mode=1,2,3, ... NEOF+1)
    vaxis = cdms2.createAxis(range(1, NEOF + 1), id='vaxis')
    for j in range(len(variances)):
        var_acc = (cvar[j].copy())
        var_acc[1:] = cvar[j][1:] - cvar[j][:-1]
        # variance accounted for ceof input variable
        var_acc = var_acc * 100
        # set variance accounted variable meta data attributes
        var_acc = cdms2.createVariable(var_acc)
        var_acc.id = '_'.join(['var_acc', vnames[j], season])
        var_acc.setAxis(0, vaxis)
        var_acc.comments = ''
        # write the variance accounted variable into nc file.
        out.write(var_acc)
        # make memory free
        del var_acc
    # end of for j in range(len(variances)):

    if season == 'all':
        # PC Time Series Computation For The Purpose Of
        # Computing Amplitude And Phases
        # Computating pcts only for the all season.

        # get the pcs of ceof input variables
        pcs = eofobj.pcs(pcscaling=0, npcs=NEOF)
        pctime = pcs.getTime()

        for i in range(NEOF):
            # extract the pcs 0, 1, 2, 3,...,NEOF-1.
            pcs_i = pcs[::, i]
            pcs_i.id = 'pcs' + str(i + 1)
            pcs_i.comments = ''
            # do the normalized pcs 0, 1, 2, 3,...,NEOF-1.
            pcs_std_i = genutil.statistics.std(pcs_i, axis='t')
            pcs_mean_i = cdutil.averager(pcs_i, axis='t')
            norm_pcs_i = (pcs_i - pcs_mean_i) / pcs_std_i
            norm_pcs_i = cdms2.createVariable(norm_pcs_i)
            norm_pcs_i.id = 'norm_pcs' + str(i + 1)
            norm_pcs_i.setAxis(0, pctime)
            norm_pcs_i.comments = ''
            pcs_std_i = cdms2.createVariable(pcs_std_i, id='pcs_std_' + str(i + 1))
            # write the pcs, normalize pcs 0, 1, 2, 3,...,NEOF-1 into nc file.
            out.write(pcs_i)
            out.write(norm_pcs_i)
            out.write(pcs_std_i)
        # end of for i in range(NEOF):

        # make memory free
        del pcs
    # end of if season == 'all':
    out.close()
    # make memory free
    del eofobj
    print "Stored all the ceof variables into nc file", outfile


# end of def genCeofVars(infiles, outfile, ...):


def genProjectedPcts(infile, outfile, eofobj, lat=(-15, 15, 'cob'), NEOF=4, season='all', **kwarg):
    """

    KWargs:

        obs_pcts_std: If this keyword passed with list of observed ceof pctime series std,
        then the normalized projected pseudo time series will be divided by obs pcts std.
        Otherwise it will computed its own std.

    Date : 08.08.2013
    """

    vnames = []
    normals = []
    # CAUTION : This is the correct order of variables to do ceof.
    # If order has changed, then it produces with multiplied by -1 in eofs
    # and pcs1. ('olr', 'u200', 'u850') is the correct order to do MJO works.
    # If 'precipitation' has passed instead of 'olr', then just replace the
    # olr position.
    correctOrderVars = ['olr', 'u200', 'u850']
    obs_vars_std = kwarg.get('obs_vars_std', {})
    obs_pcts_std = kwarg.get('obs_pcts_std', [])
    f = cdms2.open(infile)
    for var in correctOrderVars:
        data = f(var, squeeze=1)
        axlist = data.getAxisList()
        # get the normalized data & std of meridionally averaged data
        if obs_vars_std:
            mstd = obs_vars_std[var]  # get observed variable's std
        else:
            mstd = genutil.statistics.std(data, axis='t')
        normal = data / mstd
        normal.setAxisList(axlist)
        normal.id = var
        # append the normalize data into normals list
        normals.append(normal)
        # store the input variable generic name
        vnames.append(var)
        # make memory free
        del normal, data
    # end of for name, varName, infile in infiles:
    f.close()
    print "applying projected fileds"
    proj_field = eofobj.projectField(normals, neofs=NEOF)(squeeze=1)
    # make memory free
    del normals

    out = cdms2.open(outfile, 'w')
    pctime = proj_field.getTime()
    for i in range(NEOF):
        # extract the pcs 0, 1, 2, 3,...,NEOF-1.
        pcs_i = proj_field[::, i]
        pcs_i.id = 'pcs' + str(i + 1)
        pcs_i.long_name = 'projected pc time series'
        pcs_i.comments = ''  #'NCMRWF T254 model pseudo projected ceof%s pcts. The first projected pcts is given by proj_pcts1=proj_field[::, 0]' % str(tuple(vnames))
        # do the normalized pcs 0, 1, 2, 3,...,NEOF-1.
        if obs_pcts_std:
            pcs_std = obs_pcts_std[i]  # get observed pcts std
        else:
            pcs_std = genutil.statistics.std(pcs_i, axis='t')
        pcs_mean_i = cdutil.averager(pcs_i, axis='t')
        norm_pcs_i = (pcs_i - pcs_mean_i) / pcs_std
        norm_pcs_i = cdms2.createVariable(norm_pcs_i)
        norm_pcs_i.id = 'norm_pcs' + str(i + 1)
        norm_pcs_i.setAxis(0, pctime)
        norm_pcs_i.long_name = 'projected normalized pc time series'
        norm_pcs_i.comments = ''  #'NCMRWF T254 model pseudo projected ceof%s Normalized pcts. The first normalized projected pcts is given by nomproj_pcts1=normalized_proj_field[::, 0]' % str(tuple(vnames))
        # write the pcs, normalize pcs 0, 1, 2, 3,...,NEOF-1 into nc file.
        out.write(pcs_i)
        out.write(norm_pcs_i)
    # end of for i in range(NEOF):
    # make memory free
    del proj_field

    out.close()
    print "Projected pcts has written into nc file", outfile

    # end of def genProjectedPcts(eofobj, *data, **kwarg):
