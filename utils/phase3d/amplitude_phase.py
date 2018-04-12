import cdms2, numpy, os, sys
import trig


def getMjoAmplitudePhases(pcs1, pcs2):
    """
    pcs1 - pcs1 or normalized pcs1. It must have timeAxis also.
    pcs2 - pcs2 or normalized pcs2.

    Updated Date : 11.06.2013

    """

    amp = numpy.ma.sqrt((pcs1**2) + (pcs2**2))
    phases = []

    for i in xrange(len(amp)):
        # get the actual half quadrant of the circle of the start x, y points
        # of pcs1, pcs2.
        hq = trig.getHalfQuadrantOfCircle(pcs1[i], pcs2[i])
        if hq == -1:
            phase = -1
        else:
            # adding 4 to make mjo phase.
            phase = (hq + 4) % 8
            if phase == 0: phase = 8
        # end of if hq == -1:
        phases.append(phase)
    # end of for i in xrange(len(amp)):

    timeAxis = pcs1.getTime()
    amp = amp.reshape((len(amp), 1))
    phases = numpy.array(phases)
    phases = phases.reshape((len(phases), 1))
    amp_pha = numpy.concatenate((amp, phases), axis=1)

    # making memmory free
    del amp, phases, pcs1, pcs2

    amp_pha = cdms2.createVariable(amp_pha, id='amppha')
    amp_pha.long_name = 'amplitude phases'
    amp_pha.comments = 'see axis comment also'
    apAxis = cdms2.createAxis([0, 1], id='amp_pha')
    apAxis.comments = """amplitudes and its phases.
    We can access amplitudes or phases alone by specifying either 0 or 1.
    eg: >>> data(amp_pha=0) # it will extract only amplitudes
        >>> data(amp_pha=1) # it will extract only phases
    By default it will extract both amplitudes and phases.
    Along with this you can sepcify time axis also. """
    amp_pha.setAxisList([timeAxis, apAxis])

    return amp_pha


# end of def getMjoAmplitudePhases(pcs1, pcs2):


def genMjoAmplitudePhases(infile, outfile, pcs1VarName='pcs1', pcs2VarName='pcs2', pcs2Sign=-1, **kwarg):
    """

    Date : 11.06.2013
    """

    f = cdms2.open(infile)
    pcs1 = f(pcs1VarName)
    pcs2 = f(pcs2VarName) * pcs2Sign
    f.close()

    amp_pha = getMjoAmplitudePhases(pcs1, pcs2)
    amp_pha.comments = 'see axis comment also'
    out = cdms2.open(outfile, 'w')
    out.write(amp_pha)
    out.close()
    print "Written amp_pha into nc file", outfile


# end of def genMjoAmplitudePhases(infile, ...):
