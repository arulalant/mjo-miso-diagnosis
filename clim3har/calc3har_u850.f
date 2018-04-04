      program calc3har
      implicit none

c Calculates the mean and first 3 harmonics of the annual cycle
c of the gridded analysis data based on the period between and including
c yr1 and yr2. This data may be of any daily time resolution
c (e.g. 4* daily reanalysis), but for input the routine does not
c distinguish between the time of day that the data was recorded.
c The first step is to compute a seasonal cycle of 365 daily averages.
c A Fast FFT is then used to calculate the mean and first 3 harmonics
c of this 365-day c time series. This mean value plus the 6
c coefficients representing the 3 harmonics are saved in
c 3 seperate bin files.
      integer nps,nbns,NLAT,NLON,i,j,lon,lat
      parameter (nps=366,nbns=nps/2,NLON=144,NLAT=73)
      integer yr1,yr2,ny,nm,nd,nh,ncnt
      real xx(NLON,NLAT),xxa(NLON,NLAT,nps),xxm(nps),Pi,level
      real var3har(NLON,NLAT),a1(nbns),b1(nbns),v1(nbns),totvar,mean
      real anom(NLON,NLAT),mm(NLON,NLAT),aa(3,NLON,NLAT),bb(3,NLON,NLAT)
      parameter (Pi=3.1415927)
      integer iunit,ivar,rl1,rl2,rl3,totrlen,nn(nps),idx
      real julian,tt

      character*(*) dir1
      parameter(dir1='/gpfs4/home/arulalan/MJO/climatology/Daily/u850/')

c Input file
      open(11,file=dir1//'u850.mjo.daily.climatology.1979-2005.bin',
     #        form='unformatted',access='stream',status='old')

c Output files
      INQUIRE(iolength=rl1)mm
      INQUIRE(iolength=rl2)aa
      INQUIRE(iolength=rl3)bb
      open(20,file=dir1//'u850.clim.mean.1979-2005.bin',
     #        access='direct',recl=rl1,status='replace')
      open(21,file=dir1//'u850.clim.aa.1979-2005.bin',
     #        access='direct',recl=rl2,status='replace')
      open(22,file=dir1//'u850.clim.bb.1979-2005.bin',
     #        access='direct',recl=rl3,status='replace')
c    Initialize
      read(11) xxa

c****** Calculate 3 harmonics using FFT.....**********
      print*,'Doing FFTs'

      do 75 lat=1,NLAT
      do 75 lon=1,NLON

       do 65 i=1,nps
        xxm(i)=xxa(lon,lat,i)
 65    continue

       call fastft (xxm,nps,a1,b1,v1,totvar,mean)

       mm(lon,lat) = mean
       do j=1,3
        aa(j,lon,lat)=a1(j)
        bb(j,lon,lat)=b1(j)
       enddo

 75   continue

c   *** Write mean + coefficients of first 3 harmonics to file ***
      write(20,rec=1) mm
      write(21,rec=1) aa
      write(22,rec=1) bb
      close(20)
      close(21)
      close(22)
      close(11)

      STOP

2500  END
c
c --------------------------------------------------------------------------
      SUBROUTINE fastft(ts,N,a,b,v,totvar,mean)
      implicit none

c   Uses the fftpack routines.
c   N.b. If many FFT calls will be made with the same N, then use fastftM.f
c
c   The a and b are the cosine and sine coefficients respectively.
c   v is the variance in each bin. totvar is the total variance.
c   N, the length of the series, can be either even or odd with numco=N/2

      integer N,numco,i
      real ts(N),coef(20000),a(N/2),b(N/2),v(N/2)
      real totvar,mean,wsave(40000)     !>2*N+15

      numco = N/2       ! This works if N is either odd or even.
      totvar = 0.0

      do i=1,N
       coef(i)=ts(i)
      enddo

c Initialize the FFT routine (wsave contains the prime factors of N).
c N.b. If you are doing many calls of FFT with the same N, then it is
c best to put the call to rffti in the main program....see fastftM.f
      call rffti(N,wsave)
c Do the FFT.
      call rfftf(N,coef,wsave)

      do i=1,N
         coef(i) = coef(i) / (float(N)/2.)
      enddo

      mean = coef(1)/2.

      do 950  i = 1, numco-1
       a(i) = coef((i)*2)
       b(i) = -coef((i)*2+1)
       v(i) = (a(i)**2 + b(i)**2) / 2.0
c    Note that the variance of a sine or cosine wave is 1/2
       totvar = totvar + v(i)
 950  continue

        if (float(N/2).eq.(float(N)/2.)) then
c get 'a' (cos coef) for the Nyquist frequency, valid if n is even.
         a(numco) = coef(2*numco) / 2.0
         b(numco) = 0.0
         v(numco) = a(numco) ** 2
         totvar = totvar + v(numco)
        else
c get 'a' (cos coef) and 'b' (sin coef) for the Nyquist
c frequency, valid if N is odd.
         a(numco) = coef(2*numco)
         b(numco) = coef(2*numco+1)
         v(numco) = (a(numco)**2 + b(numco)**2) / 2.0
         totvar = totvar + v(numco)
        endif

 970   continue
      return
      END
c -------------------------------------------------------------------

      REAL FUNCTION julian(nm,nd,nh)
c   Computes a floating-point julian day. A fractional day
c   gives information about the hour of day.
c   This routine returns the same value for the 29th of Feb
c   as for the 1st of March.
      integer nm,nd,nh,mon(12)
      data mon/31,28,31,30,31,30,31,31,30,31,30,31/
      julian = 0.
      do i=1,nm-1
       julian = julian + float(mon(i))
      enddo
      julian = julian+float(nd)+float(nh)/24.
      END
