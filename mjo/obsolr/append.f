      program appendOLR
      implicit none

c This program reads-in the file of (global) OLR data that was
c most recently ftped from NCEP. Look at README.NCEPolr for
c information on the format of this file. This data is then
c appended to the file    olr.total.NCPEPuninterp.DN.b
c The format of the data in the new file is still day/night, but 145*73,
c and switched to the SP -> NP format.
c
c Note that the individual grids from NCEP may* have spatially
c interpolated data in the place of missing data. These interpolated
c values are given negative values. For the purpose of real-time
c monitoring, these interpolated values are allowed, however at a
c later time they should be better replaced with some temporally
c interpolated values, as in Liebmann and Smith (1996). There may
c also be completely missing data which is given the value of -999.9.
c These are also allowed by this program.
c
c (*It turns out that NCEP appears to be no longer spatially
c interpolating the grids.)
c
c Note that the output file will continue to grow by this
c program. The program cutNCEPolr.f will truncate the beginning
c of it, if you wish.

c 
c Finally, note that the time refers to a Greenwich day (i.e., GMT).

c   Input format (NP->SP)
      integer*4 inite(144,72), iday(144,72)
      real*4    fday(144,71), fnite(144,71)
      integer i,j, totmissD, totinterpD, interpormissD(144,73)
      integer totmissN, totinterpN, interpormissN(144,73)
c   Output format (SP->NP)
      real olroutD(145,73),olroutN(145,73),xlat
      integer ihd(10),nyo,nmo,ndo
      character*9 fname

      print*,'RUNNING append.f'

      totmissD = 0
      totmissN = 0
      totinterpD = 0
      totinterpN = 0
      do j=1,73
      do i=1,144
       interpormissD(i,j) = 0
       interpormissN(i,j) = 0
      enddo
      enddo

      open(10,file='filename')  ! the filename of most recently ftp-ed file.
      read(10,10,end=777,err=777) fname
 10    format(a9)
      read(fname,11,end=777,err=777) nyo,nmo,ndo
 11   format(1x,i4,i2,i2)

      print*,'Date according to filename is        ',nyo,nmo,ndo

      open(1,file=fname)
      open(2,file=
     &'/g/ns/cw/poama/data-1/mwheeler/maproomdata/OLR/'//
     &  'olr.total.NCEPuninterp.DN.b',
     &   access='append',form='unformatted')

c------ read "night" pass OLR data
      read(1,105,end=888,err=888) ((inite(I,J),I=1,144),J=1,72)
 105  format(144I6)
 
c------ read "day" pass OLR data
      read(1,105,end=888,err=888) ((iday(I,J),I=1,144),J=1,72)
 
       ihd(1) = inite(3,1)
       ihd(2) = inite(4,1)
       ihd(3) = inite(5,1)
       print*,'Date according to header of NCEP file',
     #                     ihd(1),ihd(2),ihd(3)

c     *may have to occassionally comment-out the following lines*
       if(ihd(1).ne.nyo.or.ihd(2).ne.nmo.or.ihd(3).ne.ndo) then
        open(3,file='stop.out')
        write(3,*) 'STOP process because date of header of NCEP file'
        write(3,*) 'does not match the date according to the filename.'
        close(3)
        open(4,file='stop')
        write(4,*) 'STOP'
        close(4)
        STOP
       endif
c     ***

      do 300 j=2,72
         do 200 i=1,144
         if(iday(i,j).eq.-9999) then
           fday(i,j-1)=-999.9
           totmissD=totmissD+1
           interpormissD(i,73-j+1)=1
         else
           if(iday(i,j).lt.0) then
c           {decide if you want to accept interpolated values}
             fday(i,j-1)= -1. * float(iday(i,j))/10.
             totinterpD=totinterpD+1
             interpormissD(i,73-j+1)=1
           else
             fday(i,j-1)=float(iday(i,j))/10.
           endif
         endif
         if(inite(i,j).eq.-9999) then
           fnite(i,j-1)=-999.9
           totmissN=totmissN+1
           interpormissN(i,73-j+1)=1
         else
           if(inite(i,j).lt.0) then
c           {decide if you want to accept interpolated values}
             fnite(i,j-1)=(-1.) * float(inite(i,j))/10.
             totinterpN=totinterpN+1
             interpormissN(i,73-j+1)=1
           else
             fnite(i,j-1)=float(inite(i,j))/10.
           endif
         endif
c 
         olroutD(i,73-j+1) = fday(i,j-1)
         olroutN(i,73-j+1) = fnite(i,j-1)

200      continue

         olroutD(145,73-j+1)=olroutD(1,73-j+1)
         olroutN(145,73-j+1)=olroutN(1,73-j+1)

300      continue

c        Fill-in the NP and SP values
         do i=1,145
          if(iday(26,1).eq.-9999) then
           olroutD(i,1)= -999.9
           interpormissD(i,1)=1 
          elseif(iday(26,1).lt.0) then
           olroutD(i,1)= -1.*float(iday(26,1))/10.
           interpormissD(i,1)=1 
          else
           olroutD(i,1)= float(iday(26,1))/10.
          endif
          if(inite(26,1).eq.-9999) then
           olroutN(i,1)= -999.9
           interpormissN(i,1)=1 
          elseif(inite(26,1).lt.0) then
           olroutN(i,1)= -1.*float(inite(26,1))/10.
           interpormissN(i,1)=1 
          else
           olroutN(i,1)= float(inite(26,1))/10.
          endif
          if(iday(25,1).eq.-9999) then
           olroutD(i,73)= -999.9
           interpormissD(i,1)=1 
          elseif(iday(25,1).lt.0) then
           olroutD(i,73)= -1.*float(iday(25,1))/10.
           interpormissD(i,1)=1 
          else
           olroutD(i,73)= float(iday(25,1))/10.
          endif
          if(inite(25,1).eq.-9999) then
           olroutN(i,73)= -999.9
           interpormissN(i,1)=1 
          elseif(inite(25,1).lt.0) then
           olroutN(i,73)= -1.*float(inite(25,1))/10.
           interpormissN(i,1)=1 
          else
           olroutN(i,73)= float(inite(25,1))/10.
          endif
         enddo

         if (ihd(1).lt.1900) ihd(1)=ihd(1)+1900
         if (nyo.lt.1900) nyo=nyo+1900
         write(2) nyo,nmo,ndo,33,totmissD,totinterpD
         write(2) olroutD
         write(2) nyo,nmo,ndo,99,totmissN,totinterpN
         write(2) olroutN

         print*,'************ DAY PASS OF SATELLITE *************'
         print*,'Number of missing is',totmissD,' out of',144*71
         print*,'Number of interp  is',totinterpD,' out of',144*71
         print*,'       (These values dont include NP or SP)'
         do j=73,1,-2
222       format(f5.1,' ',72(i1))
          xlat=float(j-1)*2.5-90.              !latitude in degrees
          write(*,222) xlat,(interpormissD(i,j),i=1,144,2)
         enddo
         print*
         print*,'************ NIGHT PASS OF SATELLITE *************'
         print*,'Number of missing is',totmissN,' out of',2*144*71
         print*,'Number of interp  is',totinterpN,' out of',2*144*71
         do j=73,1,-2
          xlat=float(j-1)*2.5-90.              !latitude in degrees
          write(*,222) xlat,(interpormissN(i,j),i=1,144,2)
         enddo

        STOP

777     open(3,file='stop.out')
        write(3,*) 'STOP process because of reading error 777'
        write(3,*) 'Something wrong with filename of NCEP file'
        close(3)
        open(4,file='stop')
        write(4,*) 'STOP'
        close(4)
        STOP

888     open(3,file='stop.out')
        write(3,*) 'STOP process because of reading error 888'
        write(3,*) 'Something wrong with NCEP file'
        close(3)
        open(4,file='stop')
        write(4,*) 'STOP'
        close(4)
        STOP

         end 
