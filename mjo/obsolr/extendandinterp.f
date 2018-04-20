      program extend
      implicit none

c This program is designed to be run each day.
c It reads in the most recent couple (or more) of
c years of Brant interpolated data and adds to it
c what is available from the NCEP site (uninterpolated).
c The program also interpolates the NCEP OLR data so
c that it can be directly used by the realtime filtering
c and plotting routines.
c Interpolation is done in time only (i.e. this is not as
c sophisticated as Liebmann and Smith (BAMS, 1996), but they
c have the luxury of working on the data not in real time).
c It is applied separately to the day and night data (as
c stored in NCEPuninterp.DN.b file), and then the data
c is daily averaged, and added to the Binterp data.

      integer nyBIlast,nmBIlast,ndBIlast,yrout
      real ncepD(145,73), ncepN(145,73), binterp(145,73)

      integer nmiss          ! Maximum number of days of uninterpolated
      parameter (nmiss=2000)  ! DN data that we want to add to end.
      real xav(145,73),xD(145,73,nmiss),xN(145,73,nmiss)
      real xmissD(nmiss),xmissN(nmiss)
      parameter(yrout=1998)

      integer i,j,tim,npts,ny(nmiss),nm(nmiss),nd(nmiss)

      character*(*) dir1
      parameter(dir1='../interpolated/')

C Input file of uninterpolated Day/Night data from NCEP
      open(1,file=dir1//'olr.total.NCEPuninterp.DN.b',
     &       form='unformatted',status='old')
c Input file of Brant interpolated data from CDC - has better interpolation
      open(2,file=dir1//'olr.total.96toEnd.Binterp.1x.b',
     &       form='unformatted',status='old')

c Output file of the two above joined together, with some interpolation.
      open(3,file=dir1//'olr.total.98toRealtime.1x.b',
     &       form='unformatted')

c    Read-in and write-out (to its end) Brant's interpolated data
 11   continue
        read(2,end=22) ny(1),nm(1),nd(1)
        read(2) binterp
        if(ny(1).ge.yrout) then
         write(3) ny(1),nm(1),nd(1),12
         write(3) ((binterp(i,j),i=1,145),j=1,73)
        endif
      goto 11

 22   nyBIlast=ny(1)
      nmBIlast=nm(1)
      ndBIlast=nd(1)
      print*,'The end of the Brant interp data is ',
     &                            nyBIlast,nmBIlast,ndBIlast


c   Now read and discard the NCEP data from before the date
c   of the last Binterp data.
 33   continue
        read(1,end=997) ny(1),nm(1),nd(1)
        read(1,end=997) ncepD
        read(1,end=997) ny(1),nm(1),nd(1)
        read(1,end=997) ncepN
        if(ny(1).eq.nyBIlast.and.nm(1).eq.nmBIlast.and.
     #     nd(1).eq.ndBIlast)       go to 44
      goto 33

c     Now we prepare 2 arrays of data for interpolation. 1st grid in each
c     is the last interpolated data of Brant's. (It is not ideal doing this,
c     but it is too difficult doing anything else.)
 44   do j=1,73
       do i=1,145
         xD(i,j,1) = binterp(i,j)
         xN(i,j,1) = binterp(i,j)
       enddo
      enddo

      npts = 1  ! this counts how many extra days of NCEP uninterp data we have.

      do tim=2,nmiss
       read(1,end=99) ny(tim),nm(tim),nd(tim)
       read(1) ncepD
       read(1) ny(tim),nm(tim),nd(tim)
       read(1) ncepN
       npts = npts + 1
       do j=1,73
        do i=1,145
          xD(i,j,tim) = ncepD(i,j)
          xN(i,j,tim) = ncepN(i,j)
        enddo
       enddo
      enddo

 99   if (npts.ge.nmiss-1) then
        print*,'****ERROR with npts too large in extendandinterp.f**'
        open(3,file='stop.out')
        write(3,*)
     #'STOP process because npts too large in extendandinterp'
        close(3)
        open(4,file='stop')
        write(4,*) 'STOP'
        close(4)
        STOP
      else
        print*,'Number of days of OLR beyond Binterp, npts=',npts
      endif

       do j=1,73
        do i=1,145
          do tim=1,npts
c            N.b. any total OLR value outside these bounds is likely erroneous.
             if(xD(i,j,tim).lt.50.or.xD(i,j,tim).gt.400) then
                    xD(i,j,tim) = 1.e36
             endif
             if(xN(i,j,tim).lt.50.or.xN(i,j,tim).gt.400) then
                    xN(i,j,tim) = 1.e36
             endif
             xmissD(tim) = xD(i,j,tim)
             xmissN(tim) = xN(i,j,tim)
          enddo
c INTERPOLATE and EXTRAPOLATE over missing data!
         call remmis(xmissD,npts)
         call remmis(xmissN,npts)
          do tim=1,npts
              xD(i,j,tim) = xmissD(tim)
              xN(i,j,tim) = xmissN(tim)
          enddo
        enddo
       enddo

c Now write the newly interpolated data out

       do tim=2,npts
         do j=1,73
         do i=1,145
          xav(i,j)=(xD(i,j,tim)+xN(i,j,tim))/2.
         enddo
         enddo
        write(3) ny(tim),nm(tim),nd(tim),12
        write(3) ((xav(i,j),i=1,145),j=1,73)
        if (tim.eq.npts) then
         print*,'Extending with NCEP OLR until',ny(tim),nm(tim),nd(tim)
        endif
       enddo

       go to 1000

997    print*,'Came to an unexpected eof when reading the uninterp data'
       print*,'Last day read was ',ny(1),nm(1),nd(1)
        open(3,file='stop.out')
        write(3,*)
     #'STOP extandandinterp bcse cme to unexpected eof in uninterp data'
        write(3,*) 'Last day read was ',ny(1),nm(1),nd(1)
        close(3)
        open(4,file='stop')
        write(4,*) 'STOP'
        close(4)

1000   stop
       end

c--------------------------------------------------------------
      SUBROUTINE REMMIS(PTS, NTIME)
c Removes missing data (defined as values > 1.E30) from PTS
c by both interpolation, and some extrapolation at the end, if needed.
      REAL PTS(ntime)
      INTEGER  NTIME, ITIME, BCOUNT, LEFT, RIGHT
      LOGICAL DOBEG, INMISS, FNDGD1, FEQUAL, FNEQUAL
C
C BCOUNT IS COUNT OF MISSING AT BEGINNING OF TIME SERIES(T.S.), IF ANY
C LEFT IS INDEX OF LAST GOOD POINT BEFORE SOME ARE MISSING IN MIDDLE OF T.S.
C RIGHT IS INDEX OF FIRST GOOD PT. AFTER SOME ARE MISSING IN MIDDLE OF T.S.
C DOBEG IS TRUE WHEN WE HAVE MISSING AT BEGINNING OF T.S. TO TAKE CARE OF
C INMISS IS TRUE IF WE ARE GOING THRU SOME MISSING IN MIDDLE OF T.S.
C FNDGD1 IS TRUE WHEN WE HAVE FOUND FIRST GOOD PT. IN T.S.
C
C
            BCOUNT = 0
            DOBEG = .FALSE.
            INMISS = .FALSE.
            FNDGD1 = .FALSE.
            DO 10 ITIME = 1, NTIME, 1
               IF (ITIME .EQ. 1) THEN
                  IF (PTS(ITIME).gt.(1.0e30)) THEN
                     DOBEG = .TRUE.
                  ELSE
                     FNDGD1 = .TRUE.
                  ENDIF
               ELSE
                  IF (PTS(ITIME).gt.(1.0e30)) THEN
                     IF (.NOT. (DOBEG .AND. .NOT. FNDGD1)) THEN
                        IF (.NOT. INMISS) THEN
                           INMISS = .TRUE.
                           LEFT = ITIME - 1
                        ENDIF
                     ENDIF
                  ELSE
C
C IS A GOOD POINT
C
                     IF (DOBEG .AND. .NOT. FNDGD1) THEN
                        FNDGD1 = .TRUE.
                        BCOUNT = ITIME - 1
                     ELSE IF (INMISS) THEN
                        INMISS = .FALSE.
                        RIGHT = ITIME
                        CALL INTERP(PTS, ntime, LEFT, RIGHT)
                     ENDIF
                  ENDIF
               ENDIF
 10         CONTINUE
            IF (INMISS) THEN
               CALL FILEND(PTS, LEFT, NTIME)
            ENDIF
            IF (DOBEG) THEN
               CALL FILBEG(PTS, BCOUNT)
            ENDIF
      RETURN
      END
C
      SUBROUTINE INTERP(PTS, ntime, LEFT, RIGHT)
      REAL PTS(ntime), INCDIF
      INTEGER LEFT, RIGHT, ITIME
C
      INCDIF=(PTS(RIGHT)-PTS(LEFT)) /
     +         (RIGHT - LEFT)
      DO 10 ITIME = LEFT + 1,  RIGHT - 1,  1
         PTS(ITIME) = PTS(LEFT) +
     +                            (ITIME - LEFT)  *  INCDIF
 10   CONTINUE
      RETURN
      END
C
      SUBROUTINE FILEND(PTS, LSTGD, NTIME)
      REAL PTS(ntime), SUM
      INTEGER LSTGD, NTIME, ITIME, ITIME2
C
      DO 10 ITIME = LSTGD + 1,  NTIME,  1
         SUM = 0.0

         DO 20 ITIME2 = ITIME - 5,  ITIME - 1,  1
            SUM = SUM + PTS(ITIME2)
 20      CONTINUE
         PTS(ITIME) = SUM / 5.0
 10   CONTINUE
      RETURN
      END
C
      SUBROUTINE FILBEG(PTS, BCOUNT)
      REAL PTS(bcount), SUM
      INTEGER ITIME, ITIME2, BCOUNT
C
      DO 10 ITIME = BCOUNT, 1, -1
         SUM = 0.0
         DO 20 ITIME2 = ITIME + 1,  ITIME + 5, 1
            SUM = SUM + PTS(ITIME2)
 20      CONTINUE
         PTS(ITIME) = SUM / 5.0
 10   CONTINUE
      RETURN
      END
C
C.............................................................
      LOGICAL FUNCTION FEQUAL(FPN1, FPN2, DELTA)
      REAL FPN1, FPN2, DELTA
C
      IF (ABS(FPN1-FPN2) .LE. DELTA) THEN
         FEQUAL = .TRUE.
      ELSE
         FEQUAL = .FALSE.
      ENDIF
      RETURN
      END
C.............................................................
      LOGICAL FUNCTION FNEQUAL(FPN1, FPN2, DELTA)
      REAL FPN1, FPN2, DELTA
C
      IF (ABS(FPN1-FPN2) .GT. DELTA) THEN
         FNEQUAL = .TRUE.
      ELSE
         FNEQUAL = .FALSE.
      ENDIF
      RETURN
      END
