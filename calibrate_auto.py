# CASA 4.7.0 required for spectra!
# Automatically (mostly) calibrates a JVLA observation.
# Must be run with an internet connection to determine antenna offsets and opacity measurements.
DEBUG = True
# Definitions
# Observation
flux_calibrator = '3C286'
flux_calibrator_band = 'K'
myconfig = 'C'                                                      # VLA array configuration used for the observation.
myband = 'K'                                                        # Observing band.

# MS specific
msfile = '10B-245_sb2156325_1.55500.189165324075.ms'                # Original MS file.
myfield = '0,2,4'                                                   # Fields to split into separate file.
myfluxref, myphaseref, mytarget = '2', '1', '0'                     # The _NEW_ indices of the fields (starting from 0 on the lowest field).
myspw = '2~3'                                                       # Spectral windows of interest.
mssplit = '10B-245.srcs_K.ms'                                       # MS file with the interesting sources from `myfield`.
msscans = '10B-245.srcs_K.ms.txt'                                   # Text file to write `listobs` output to.
mstarget = 'target_K.ms'                                            # MS file of the target.
myimage = 'target_K_image'                                          # Image.
mycube = 'target_K_cube'                                            # Cube.
mycontsub = 'target_K.ms.contsub'                                   # Continuum subtraction.
skymodel = 'target_K.model'                                         # Sky model.
mymask = 'target_K.mask'                                            # Mask.
myrefant = 'ea05'                                                   # Reference antenna.

# Spectral line and imaging parameters.
myrestfreq = "23.38348GHz"                                          # Spectral line redshifted rest frequency.
mylinespw = '5'                                                     # spw containing the line.
mylinechannels = '20~40'                                            # Channels in the selected spw containing the line.
myfitorder = 1
mylinechannels_spectrum = '340~360'                                 # Range of channels containing the line in the full spectrum.

myimsize = 256
##############################################################
# DO NOT EDIT BELOW THIS LINE // DO NOT EDIT BELOW THIS LINE #
##############################################################
# Telescope parameters
# Band center frequencies in GHz based on https://science.nrao.edu/facilities/vla/docs/manuals/oss2013B/performance/bands
vla_bands = {'4':0.071, 'P':0.35, 'L':1.5, 'S':3.0, 'C':6.0, 'X':10.0, 'Ku':15.0, 'K':22.25, 'Ka':33.25, 'Q':45.0}
# Baseline lengths in km taken from https://science.nrao.edu/facilities/vla/docs/manuals/oss/performance/resolution
array_baseline_max = {'A':36.4, 'B':11.1, 'C':3.4, 'D':1.03}
# Calculate the field of view and angular resolution.
mylambda = (299792458) / (vla_bands[myband] * 1e9)
# VLA dishes are 25m.
myfov = (mylambda / 25) * 206265
myresolution = (mylambda / (array_baseline_max[myconfig]*1e3)) * 206265
print 'Field of view [arsec]: ', myfov
print 'Angular resolution [arscec]: ', myresolution

import os
import sys

'''
The Python variable 'mysteps' will control which steps
are executed when you start the script using
   execfile('scriptForCalibration.py')
e.g. setting
   mysteps = [2,3,4]
before starting the script will make the script execute
only steps 2, 3, and 4
Setting mysteps = [] will make it execute all steps.
'''
# Calibration steps
thesteps = [0]
step_title = {0: 'Set the variables and initial split (split)',
                1: 'A priori correction of opacity, antenna elevation and antenna positions (gencal)',
                2: 'Flag bad data (flagdata)',
                3: 'Insert model of the flux calibrator (setjy)',
                4: 'Short phase correction (gaincal)',
                5: 'Delay correction (gaincal)',
                6: 'Bandpass calibration (bandpass)',
                7: 'Gain (Amplitude and Phase) calibration (gaincal)',
                8: 'Determine the absolute flux-scale of the calibrators (fluxscale)',
                9: 'Applying the calibration tables (applycal)',
                10: 'Split target (split)',
                11: 'Continuum substraction (uvcontsub)',
                12: 'Create dirty cubes (clean)',
                13: 'Continuum subtraction (imcontsub)'}

try:
    print 'List of steps to be executed ...', mysteps
    thesteps = mysteps
except:
    while 1:
        temp  = raw_input('Variable `mysteps` not set. Execute steps 0-12? (y/n)').lower()
        if temp == 'n':
            sys.exit(0)
        elif temp == 'y':
            thesteps = range(13)
            print 'Executing steps: ', thesteps
            break
        else:
            print 'Unkown option, aborting.'
            sys.exit(0)

##############################
# Step 0: A priori splitting #
mystep = 0
if (mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]

    # Split off the selected fields into a separate MS file.
    split(vis=msfile, outputvis=mssplit, keepmms=True, field=myfield, spw=myspw, scan="", antenna="", correlation="rr,ll", timerange="", intent="", array="", uvrange="", observation="", feed="", datacolumn="data", keepflags=True, width=1, timebin="0s", combine="")

    # List properties of the created MS file.
    listobs(vis=mssplit, selectdata=True, spw="", field="", antenna="", uvrange="", timerange="", correlation="", scan="", intent="", feed="", array="", observation="", verbose=True, listfile=msscans, listunfl=False, cachesize=50, overwrite=True)
# End of step 0.             #
##############################

#######################
# Step 1: Calibration #
mystep = 1
if (mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate mean zenith opacity per spectral window.
    myTau = plotweather(vis=mssplit, doPlot=T)
    # Generate tropospheric opacity calibration table.
    gencal(vis=mssplit, caltable="opacity.cal", caltype="opac", spw="0~15",antenna="", pol="", parameter=myTau)
    # Generate ITRF (International Terrestrial Reference System) antenna position corrections calibration table.
    gencal(vis=mssplit, caltable="antpos.cal", caltype="antpos", spw="", antenna="", pol="", parameter=[])
    # Generate gain curve and efficiency calibration table.
    gencal(vis=mssplit, caltable="gaincurve.cal", caltype="gceff", spw="", antenna="", pol="", parameter=[])

    # Check if antenna position corrections were necessary.
    if os.path.exists('./antpos.cal'):
        gtables = ['opacity.cal', 'antpos.cal', 'gaincurve.cal']
        gtables2 = ['opacity.cal', 'antpos.cal', 'gaincurve.cal']
        gfields = ['', '', '']
    else:
        gtables = ['opacity.cal', 'gaincurve.cal']
        gtables2 = ['opacity.cal', 'gaincurve.cal']
        gfields = ['', '']
# End of step 1.      #
#######################

####################
# Step 2: Flagging #
mystep = 2
if (mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    execfile('./flagger.py')
# End of step 2.   #
####################

################################################
# Step 3: model of the flux calibrator - setjy #
mystep = 3
if (mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Set the flux scale for field 2 (the flux calibrator) using the model.
    setjy(vis=mssplit,field=myfluxref,spw="",selectdata=False,timerange="",scan="",intent="",observation="",scalebychan=True,standard="Perley-Butler 2010",model='%s_%s.im'%(flux_calibrator, flux_calibrator_band),modimage=None,
            listmodels=False,fluxdensity=-1,spix=0.0,reffreq="1GHz",polindex=[],rotmeas=0.0,fluxdict={},useephemdir=False,interpolation="nearest",usescratch=True,ismms=None)
# End of step 3.                               #
################################################

####################################
# Step 4: short phase calibration. #
# Calculate calibrations for the phase changing as function of time.
mystep = 4
if (mystep in thesteps):
    if DEBUG:
        print 'INTPHASE using the following calibration tables: ' + ','.join(gtables)
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate the calibrations using only a few of the central channels for each spectral window such that the response is essentially flat as function of frequency.
    gaincal(vis=mssplit,caltable="intphase.cal",field=myfluxref,spw="*:28~36",intent="",selectdata=False,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=2.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables += ['intphase.cal']
# End of step 4.                   #
####################################

########################################
# Step 5: residual delay calibration.  #
# Calculate calibrations for the phase as function of frequency.
mystep = 5
if (mystep in thesteps):
    if DEBUG:
        print 'DELAYS using the following calibration tables: ' + ','.join(gtables)
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate calibrations for the delays between antennas.
    gaincal(vis=mssplit,caltable="delays.cal",field=myfluxref,spw="*:4~60",intent="",selectdata=False,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="scan",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=2.0,solnorm=False,gaintype="K",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables += ['delays.cal']
# End of step 5.                       #
########################################

#################################
# Step 6: bandpass calibration. #
# Match shape of bandpass to spectrum of object.
mystep = 6
if (mystep in thesteps):
    if DEBUG:
        print 'BANDPASS using the following calibration tables: ' + ','.join(gtables)
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate calibrations for the bandpass.
    bandpass(vis=mssplit,caltable="bandpass.cal",field=myfluxref,spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="scan",refant=myrefant,minblperant=4,minsnr=2.0,solnorm=False,bandtype="B",smodel=[],append=False,fillgaps=0,degamp=3,degphase=3,visnorm=False,maskcenter=0,maskedge=5,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables += ['bandpass.cal']
    gtables.remove('intphase.cal')
# End of step 6.                #
#################################
##########################################
# Step 7: phase & ampltiude calibration. #
# Now use the full range of channels except the ones at the edge, because the response drops rapidly here.
mystep = 7
if (mystep in thesteps):
    if DEBUG:
        print 'FULL GAINCAL using the following calibration tables: ' + ','.join(gtables)
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate phase calibrations for the flux calibrator.
    gaincal(vis=mssplit,caltable="gainphase.cal",field=myfluxref,spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)

    # Calculate phase calibrations for the phase reference (Note `append=True`).
    gaincal(vis=mssplit,caltable="gainphase.cal",field=myphaseref,spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=True,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables += ['gainphase.cal']

    # Calculate amplitude calibrations for the flux calibrator.
    gaincal(vis=mssplit,caltable="gainamp.cal",field=myfluxref,spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="ap",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=gfields+['0', '0', '0'],interp=[],spwmap=[],parang=False)

    # Calculate amplitude calibrations for the phase reference (Note `append=True`).
    gaincal(vis=mssplit,caltable="gainamp.cal",field=myphaseref,spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="ap",append=True,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=gfields+['0', '0', '1'],interp=[],spwmap=[],parang=False)
    gtables += ['gainamp.cal']
# End of step 7.                         #
##########################################

############################################
# Step 8: absolute flux-scale calibration. #
# Transfer the calucated calibrations from the flux calibrator (field 0) to the phase calibrator (field 1). Afterwards use the calibrated flux calibrator to calibrate the phase calibrator (bootstrapping).
mystep = 8
if(mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    flux = fluxscale(vis=mssplit,caltable="gainamp.cal",fluxtable="flux.cal",reference=[myfluxref],transfer=[myphaseref],listfile="",append=False,refspwmap=[-1],gainthreshold=-1.0,antenna="",timerange="",scan="",incremental=True,fitorder=1,display=True)

    setjy(vis=mssplit,field=myphaseref,spw="",selectdata=False,timerange="",scan="",intent="",observation="",scalebychan=True,standard="fluxscale",model="",modimage=None,listmodels=False,fluxdensity=-1,spix=0.0,reffreq="1GHz",polindex=[],polangle=[],rotmeas=0.0,fluxdict=flux,useephemdir=False,interpolation="nearest",usescratch=True,ismms=None)

    gaincal(vis=mssplit,caltable="intphase2.cal",field=myphaseref,spw="*:28~36",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['intphase2.cal']

    gaincal(vis=mssplit,caltable="delays2.cal",field=myphaseref,spw="*:28~36",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="scan",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="K",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['delays2.cal']

    bandpass(vis=mssplit,caltable="bandpass2.cal",field=myphaseref,spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="scan",refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,bandtype="B",smodel=[],append=False,fillgaps=0,degamp=3,degphase=3,visnorm=False,maskcenter=0,maskedge=5,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['bandpass2.cal']

    gtables2.remove('intphase2.cal')

    gaincal(vis=mssplit,caltable="gainphase2.cal",field=myphaseref,spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['gainphase2.cal']

    gaincal(vis=mssplit,caltable="gainamp2.cal",field=myphaseref,spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="ap",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['gainamp2.cal']
# End of step 8.                           #
############################################

######################
# End of calibration #
######################

######################################
# Apply the calibration to the data. #
######################################
##################################################
# Step 9: Application of the calibration tables. #
mystep = 9
if(mystep in thesteps):
    if DEBUG:
        print 'APPLYCAL using the following calibration tables for field 0: ' + ','.join(gtables)
        print 'APPLYCAL using the following calibration tables for field 1: ' + ','.join(gtables2)
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Apply calibrations to the flux calibrator.
    applycal(vis=mssplit,field=myfluxref,spw="",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",docallib=False,callib="",gaintable=gtables,gainfield=gfields+[myfluxref, myfluxref, myfluxref, myfluxref],interp=['linear', 'linear', 'linear', 'nearest', 'nearest', 'linear', 'nearest'],spwmap=[],calwt=False,parang=False,applymode="",flagbackup=True)

    # Apply calibrations to the phase reference.
    applycal(vis=mssplit,field=myphaseref,spw="",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",docallib=False,callib="",gaintable=gtables2,gainfield=gfields+[myphaseref, myphaseref, myphaseref, myphaseref],interp=['linear', 'linear', 'linear', 'nearest', 'nearest', 'linear', 'nearest'],spwmap=[],calwt=False,parang=False,applymode="",flagbackup=True)

    # Apply calibrations to the target.
    applycal(vis=mssplit,field=mytarget,spw="",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",docallib=False,callib="",gaintable=gtables2,gainfield=gfields+[myphaseref, myphaseref, myphaseref, myphaseref],interp=['linear', 'linear', 'linear', 'nearest', 'nearest', 'linear', 'nearest'],spwmap=[],calwt=False,parang=False,applymode="",flagbackup=True)
# End of step 9.                                 #
##################################################

#######################
# Calibration applied #
#######################

######################################################
# Split off corrected target and create dirty image. #
######################################################
##################################
# Step 10: Split off the target. #
mystep = 10
if(mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    split(vis=mssplit,outputvis=mstarget,keepmms=True,field=mytarget,spw="",scan="",antenna="",correlation="",timerange="",intent="",array="",uvrange="",observation="",feed="",datacolumn="corrected",keepflags=True,width=1,timebin="0s",combine="")
    split(vis=mssplit,outputvis='phaseref.ms',keepmms=True,field=myphaseref,spw="",scan="",antenna="",correlation="",timerange="",intent="",array="",uvrange="",observation="",feed="",datacolumn="corrected",keepflags=True,width=1,timebin="0s",combine="")
    split(vis=mssplit,outputvis='fluxref.ms',keepmms=True,field=myfluxref,spw="",scan="",antenna="",correlation="",timerange="",intent="",array="",uvrange="",observation="",feed="",datacolumn="corrected",keepflags=True,width=1,timebin="0s",combine="")
# End of step 10.                #
##################################

###################################
# Step 11: Subtract continuum.    #
mystep = 11
if (mystep in thesteps):
    uvcontsub(vis=mstarget, field='', fitspw=mylinespw+':'+mylinechannels, excludechans=True, combine='spw', solint='int', fitorder=myfitorder, spw='', want_cont=False)
# End of step 11.                #
##################################

####################################################
# Step 12: Create a dirty image and/or dirty cube. #
mystep = 12
if(mystep in thesteps):
    cellsize = (myresolution / 4)
    mycell = '%.2farcsec'%(cellsize)
    # If the user has specified an image size in pixels use that value, else set it to a default value.
    try:
        myimsize = int(myimsize)
    except:
        myimsize = int(myfov / cellsize)
    print mycell
    print 'Pixel scale  ', mycell
    print 'Image size [pixels]: ', myimsize
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    if 11 in thesteps:
        print 'Creating dirty continuum subtracted cube for target.'
    else:
        print 'Creating dirty cube for target.'
    clean(vis=mstarget,imagename=mycube,outlierfile="",field="",spw="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",intent="",mode="frequency",resmooth=False,gridmode="",wprojplanes=-1,facets=1,cfcache="cfcache.dir",rotpainc=5.0,painc=360.0,aterm=True,psterm=False,mterm=True,wbawp=False,conjbeams=True,epjtable="",interpolation="linear",niter=0,gain=0.05,threshold="6.0e-5Jy",psfmode="clark",imagermode="csclean",ftmachine="mosaic",mosweight=False,scaletype="SAULT",multiscale=[],negcomponent=-1,smallscalebias=0.6,interactive=False,mask="",nchan=-1,start='22.6794GHz',width='2MHz',outframe="",veltype="radio",imsize=myimsize,cell=mycell,phasecenter="",restfreq="23.38348GHz",stokes="I",weighting="natural",robust=0,uvtaper=False,outertaper=[''],innertaper=['1.0'],modelimage="",restoringbeam=[''],pbcor=False,minpb=0.2,usescratch=True,noise="1.0Jy",npixels=0,npercycle=100,cyclefactor=1.5,cyclespeedup=-1,nterms=1,reffreq="",chaniter=False,flatnoise=True,allowchunk=False)
    #print 'Creating dirty cube for phase reference.'
    #clean(vis='phaseref.ms',imagename='phaseref_cube.ms',outlierfile="",field="",spw="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",intent="",mode="frequency",resmooth=False,gridmode="",wprojplanes=-1,facets=1,cfcache="cfcache.dir",rotpainc=5.0,painc=360.0,aterm=True,psterm=False,mterm=True,wbawp=False,conjbeams=True,epjtable="",interpolation="linear",niter=0,gain=0.05,threshold="6.0e-5Jy",psfmode="clark",imagermode="csclean",ftmachine="mosaic",mosweight=False,scaletype="SAULT",multiscale=[],negcomponent=-1,smallscalebias=0.6,interactive=False,mask="",nchan=-1,start='22.6794GHz',width='2MHz',outframe="",veltype="radio",imsize=myimsize,cell=mycell,phasecenter="",restfreq="23.38348GHz",stokes="I",weighting="natural",robust=0,uvtaper=False,outertaper=[''],innertaper=['1.0'],modelimage="",restoringbeam=[''],pbcor=False,minpb=0.2,usescratch=True,noise="1.0Jy",npixels=0,npercycle=100,cyclefactor=1.5,cyclespeedup=-1,nterms=1,reffreq="",chaniter=False,flatnoise=True,allowchunk=False)
    #print 'Creating dirty cube for flux reference.'
    #clean(vis='fluxref.ms',imagename='fluxref_cube.ms',outlierfile="",field="",spw="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",intent="",mode="frequency",resmooth=False,gridmode="",wprojplanes=-1,facets=1,cfcache="cfcache.dir",rotpainc=5.0,painc=360.0,aterm=True,psterm=False,mterm=True,wbawp=False,conjbeams=True,epjtable="",interpolation="linear",niter=0,gain=0.05,threshold="6.0e-5Jy",psfmode="clark",imagermode="csclean",ftmachine="mosaic",mosweight=False,scaletype="SAULT",multiscale=[],negcomponent=-1,smallscalebias=0.6,interactive=False,mask="",nchan=-1,start='22.6794GHz',width='2MHz',outframe="",veltype="radio",imsize=myimsize,cell=mycell,phasecenter="",restfreq="23.38348GHz",stokes="I",weighting="natural",robust=0,uvtaper=False,outertaper=[''],innertaper=['1.0'],modelimage="",restoringbeam=[''],pbcor=False,minpb=0.2,usescratch=True,noise="1.0Jy",npixels=0,npercycle=100,cyclefactor=1.5,cyclespeedup=-1,nterms=1,reffreq="",chaniter=False,flatnoise=True,allowchunk=False)
    '''
    ###############################################################################
    # Create spectra of the flux calibrator, phase reference and target.          #
    # Flux calibrator.
    specflux(imagename='fluxref_cube.ms', region='fluxref_region', chans='', stokes='I', mask='', function='flux density', unit='GHz', major='', minor='', logfile='fluxref_spectrum.txt')
    # Phase reference.
    specflux(imagename='phaseref_cube.ms', region='fluxref_region', chans='', stokes='I', mask='', function='flux density', unit='GHz', major='', minor='', logfile='fluxref_spectrum.txt')
    # Target source
    specflux(imagename='target_cube.ms', region='fluxref_region', chans='', stokes='I', mask='', function='flux density', unit='GHz', major='', minor='', logfile='fluxref_spectrum.txt')
    # End of step 12.                                                             #
    ###############################################################################
    '''
# End of step 12.                #
##################################

#######################################################
# Step 13: Perform image plane continuum subtraction. #
mystep = 13
if (mystep in thesteps):
    imcontsub(imagename=mycube+'.image', linefile='target_K_cube.imcontsub', contfile='target_K_cube.imcontinuum', fitorder=1, region='', box='', chans='0~320,>380', stokes='I')
# End of step 13.                                     #
#######################################################
