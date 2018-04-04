import os, sys, subprocess, datetime
sys.path.append('..')
from auto.cdscan_update import updateCdmlFile
# global path variables
inpath = '/gpfs3/home/umfcst/NCUM/post'
anapath = '/gpfs4/home/arulalan/MJO/NCUM_ANL'
outpath = '/gpfs4/home/arulalan/MJO/NCUM_DETERMINISTIC_FCST'
# wgrib2 = '/gpfs1/home/Libs/GNU/WGRIB2/v2.0.4/wgrib2/wgrib2'
wgrib2 = '/gpfs4/home/arulalan/Softwares/wgrib2_v2.0.7/wgrib2/wgrib2'
cdo = '/gpfs1/home/Libs/INTEL/CDO/cdo-1.6.3/bin/cdo'
checkpastdays = 1

if os.environ.has_key('MMDIAGNOSIS_STARTDATE'):
    startdate = os.environ.get('MMDIAGNOSIS_STARTDATE')
else:
    startdate = '20180317'


def createDeterministicFcstMJOinFiles(curday, nextday):
    indir = os.path.join(inpath, curday)
    nexdir = os.path.join(inpath, nextday)
    print "indir=", indir
    infile_06 = os.path.join(indir, 'um_prg_006hr_%s_00Z.grib2' % curday)
    infile_240 = os.path.join(indir, 'um_prg_240hr_%s_00Z.grib2' % curday)
    if not os.path.isfile(infile_240): return
    outfile_6hrs = os.path.join(outpath, 'um_prg_%s_6hrs.grib2' % curday)
    outfile_24hrAvg = os.path.join(outpath, 'um_prg_%s_24hrs_2p5x2p5.grib2' % curday)
    ncfile = 'um_determisitic_10days_fcst_%s_2p5x2p5.nc' % curday
    ncfilepath = os.path.join(outpath, ncfile)
    outfile_24hrAvg_2p5_files = []
    append = False
    for hr in range(6, 241, 6):
        append_option = '-append' if append else ''
        shr = str(hr).zfill(3)
        infile_hr = infile_06.replace('006hr', shr + 'hr')
        cmd1 = '%s %s -match "(:ULWRF:|:UGRD:200 mb:|:UGRD:850 mb:)" %s -grib_out %s' % (wgrib2, infile_hr,
                                                                                         append_option, outfile_6hrs)
        subprocess.call(cmd1, shell=True)
        append = True
        if hr % 24 == 0:
            day = str(hr / 24).zfill(2)
            outfile_24hrAvg_2p5 = os.path.join(outpath, 'um_prg_%s_day%s_2p5x2p5.grib2' % (day, curday))
            outfile_24hrAvg_2p5_files.append(outfile_24hrAvg_2p5)
            # makes daily average
            cmd2 = '%s %s | sort -t: -k4,4 -k5,5 -k6,6n |  %s -i %s -set_grib_type c3 -time_processing ave forecast 6hr  %s' % (
                wgrib2, outfile_6hrs, wgrib2, outfile_6hrs, outfile_24hrAvg)
            subprocess.call(cmd2, shell=True)
            append = False
            os.system('wgrib2 %s' % outfile_24hrAvg)
            # regrid to 2.5x2.5
            cmd3 = '%s %s -new_grid_winds earth -new_grid_interpolation bilinear  -new_grid_vectors none -new_grid latlon 0:144:2.5 -90:73:2.5  %s' % (
                wgrib2, outfile_24hrAvg, outfile_24hrAvg_2p5)
            subprocess.call(cmd3, shell=True)
    # end of for hr in range(6, 241, 6):

    # nc3 conversion with correct time hour as 0
    cmd4 = '%s -f nc copy -settime,00:00:00 %s %s' % (cdo, ' '.join(outfile_24hrAvg_2p5_files), ncfilepath)
    for cmd in [cmd3, cmd4]:
        subprocess.call(cmd, shell=True)
    os.remove(outfile_6hrs)
    os.remove(outfile_24hrAvg)
    for of in outfile_24hrAvg_2p5_files:
        os.remove(of)
    # update cdscan xml daily by editing xml itself.
    os.chdir(anapath)
    updateCdmlFile(ncfilepath, 'um_ana.xml', os.path.join(outpath, 'um_ana_tseries_and_fcst_10days_%s.xml' % curday))


# end of def createAnalysisMJOinFiles(curday):

if __name__ == '__main__':

    tDay = datetime.datetime.strptime(startdate, "%Y%m%d")
    lag = datetime.timedelta(days=checkpastdays)
    pDay = (tDay - lag)
    while pDay != tDay:
        pastDay = pDay.strftime('%Y%m%d')
        outfile = os.path.join(outpath, 'um_ana_tseries_and_fcst_10days_%s.xml' % pastDay)
        lag1 = datetime.timedelta(days=1)
        pDay = (pDay + lag1)
        print "outfile", outfile
        nextday = pDay.strftime('%Y%m%d')
        if not os.path.exists(outfile): createDeterministicFcstMJOinFiles(pastDay, nextday)
        print "outfile", outfile
        print "Done: ", pastDay
    # end of while pastDay != tDay:
    # end of if __name__ == '__main__':
