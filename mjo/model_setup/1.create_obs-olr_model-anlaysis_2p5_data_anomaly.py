import os, sys, subprocess, datetime
sys.path.append('../..')
from auto.cdscan_update import updateCdmlFile
# global path variables
from config.globalpaths import inpath, recentobspath, anadatapath, anaanopath, climpath, wgrib2, cdo

checkpastdays = 230

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180317'


def createObsOLRanomalies(curday, nextday):
    indir = os.path.join(inpath, curday)
    nexdir = os.path.join(inpath, nextday)
    infile_00 = os.path.join(indir, 'um_ana_000hr_%s_00Z.grib2' % curday)
    infile_06 = os.path.join(indir, 'um_ana_006hr_%s_06Z.grib2' % curday)
    infile_12 = os.path.join(indir, 'um_ana_012hr_%s_12Z.grib2' % curday)
    infile_18 = os.path.join(indir, 'um_ana_018hr_%s_18Z.grib2' % curday)
    infile_00_nextday = os.path.join(nexdir, 'um_ana_000hr_%s_00Z.grib2' % nextday)
    if not os.path.isfile(infile_00_nextday): return
    outfile_6hrs = os.path.join(anadatapath, 'um_ana_%s_6hrs.grib2' % curday)
    outfile_24hrAvg = os.path.join(anadatapath, 'um_ana_%s_24hrsAvg.grib2' % curday)
    outfile_24hrAvg_2p5 = os.path.join(anadatapath, 'um_ana_%s_daily_2p5x2p5.grib2' % curday)
    mncfile = 'um_ana_%s_daily_2p5x2p5.nc' % curday
    modelncfilepath = os.path.join(anadatapath, mncfile)
    anofile = 'obsolr_um_analysis_%s_daily_anomaly.nc' % curday
    anofpath = os.path.join(anaanopath, anofile)
    climfile = 'olr_ulwrf_u200_850_merged.clim.mean+3harm.1979-2001.nc'
    climfpath = os.path.join(climpath, climfile)
    # obsolr_datafile = 'olr.day.mean.interpolated.nc'
    obsolr_datafile = 'olr.day.mean.interpolated-WH04.nc'
    obsolrifpath = os.path.join(recentobspath, obsolr_datafile)

    obsolr = 'olr_%s.nc' % curday
    obs_model_data = 'obsolr_um_analysis_%s_daily_2p5x2p5.nc' % curday
    obsolrofpath = os.path.join(anaanopath, obsolr)
    obsmodelncfile = os.path.join(anadatapath, obs_model_data)

    cmd1 = '%s %s -match "(:UGRD:200 mb:|:UGRD:850 mb:)"  -grib_out %s' % (wgrib2, infile_00, outfile_6hrs)
    cmd2 = '%s %s -match "(:ULWRF:UGRD:200 mb:|:UGRD:850 mb:)" -append -grib_out %s' % (wgrib2, infile_06, outfile_6hrs)
    cmd3 = '%s %s -match "(:ULWRF:UGRD:200 mb:|:UGRD:850 mb:)" -append -grib_out %s' % (wgrib2, infile_12, outfile_6hrs)
    cmd4 = '%s %s -match "(:ULWRF:UGRD:200 mb:|:UGRD:850 mb:)" -append -grib_out %s' % (wgrib2, infile_18, outfile_6hrs)
    cmd5 = '%s %s -match "(:ULWRF:)" -append -grib_out %s' % (wgrib2, infile_00_nextday, outfile_6hrs)

    # makes daily average
    cmd6 = '%s %s | sort -t: -k4,4 -k5,5 -k6,6 -k3,3 |  %s -i %s -set_grib_type c3 -ave 6hr %s' % (wgrib2, outfile_6hrs,
                                                                                                   wgrib2, outfile_6hrs,
                                                                                                   outfile_24hrAvg)
    # regrid to 2.5x2.5
    cmd7 = '%s %s -new_grid_winds earth -new_grid_interpolation bilinear  -new_grid_vectors none -new_grid latlon 0:144:2.5 -90:73:2.5  %s' % (
        wgrib2, outfile_24hrAvg, outfile_24hrAvg_2p5)

    # nc3 conversion with correct time hour as 0
    cmd8 = '%s -f nc copy -settime,00:00:00 %s %s' % (cdo, outfile_24hrAvg_2p5, modelncfilepath)
    compcurday = curday[:4] + '-' + curday[4:6] + '-' + curday[6:]

    # extract curday observed olr
    cmd9 = '%s -seldate,%s %s %s' % (cdo, compcurday, obsolrifpath, obsolrofpath)

    # merge observed olr and model winds
    cmd10 = '%s merge %s %s %s' % (cdo, modelncfilepath, obsolrofpath, obsmodelncfile)
    # calculate daily anomaly for u200(model ana), u850(model ana), ulwrf(model ana), olr(obs),  variables from mean+sum of 3 harmonic climatology
    cmd11 = '%s -ydaysub %s %s %s' % (cdo, obsmodelncfile, climfpath, anofpath)
    for cmd in [cmd1, cmd2, cmd3, cmd4, cmd5, cmd6, cmd7, cmd8, cmd9, cmd10, cmd11]:
        subprocess.call(cmd, shell=True)
    os.remove(outfile_6hrs)
    os.remove(outfile_24hrAvg)
    os.remove(outfile_24hrAvg_2p5)
    os.remove(obsolrofpath)
    os.remove(modelncfilepath)
    # change working dir to anadatapath
    os.chdir(anadatapath)

    if not os.path.isfile(os.path.join(anadatapath, 'obsolr_um_analysis_data.xml')):
        # this case happens at very first time of model setup.
        subprocess.call(
            "cdscan -x obsolr_um_analysis_data.xml -r 'days since %s'  %s/*.nc" % (compcurday, anadatapath), shell=True)
    else:
        # update cdscan xml daily by editing xml itself.
        updateCdmlFile(obsmodelncfile, 'obsolr_um_analysis_data.xml')

    # change working dir to anaanopath
    os.chdir(anaanopath)
    if not os.path.isfile(os.path.join(anaanopath, 'obsolr_um_analysis_anomaly.xml')):
        # this case happens at very first time of model setup.
        subprocess.call(
            "cdscan -x obsolr_um_analysis_anomaly.xml -r 'days since %s' %s/*.nc" % (compcurday, anaanopath),
            shell=True)
    else:
        # update cdscan xml daily by editing xml itself.
        updateCdmlFile(anofile, 'obsolr_um_analysis_anomaly.xml')
    # end of def createObsOLRanomalies(curday):


if __name__ == '__main__':

    tDay = datetime.datetime.strptime(startdate, "%Y%m%d")
    lag = datetime.timedelta(days=checkpastdays)
    pDay = (tDay - lag)

    while pDay != tDay:
        pastDay = pDay.strftime('%Y%m%d')
        outfile = os.path.join(anaanopath, 'obsolr_um_analysis_%s_daily_anomaly.nc' % pastDay)
        lag1 = datetime.timedelta(days=1)
        pDay = (pDay + lag1)
        nextday = pDay.strftime('%Y%m%d')
        if not os.path.exists(outfile): createObsOLRanomalies(pastDay, nextday)
        print "Done: ", pastDay
    # end of while pastDay != tDay:
    # end of if __name__ == '__main__':
