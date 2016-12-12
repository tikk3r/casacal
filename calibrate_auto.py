# Automatically (mostly) calibrates a JVLA observation.
# Must be run with an internet connection to determine antenna offsets and opacity measurements.

# Definitions
# Observation
flux_calibrator = '3C286'
flux_calibrator_band = 'K'

# MS specific
msfile = '11B-002.sb10148166.eb10491066.56074.24292924769.ms'       # Original MS file.
myfield = '2,4,5'                                                   # Fields to split into separate file (in order of flux, phase, target).
myspw = '2~17'                                                      # Spectral windows of interest.
mssplit = '11B-002.srcs_K.ms'                                       # MS file with the interesting sources from `myfield`.
msscans = '11B-002.srcs_K.ms.txt'                                   # Text file to write `listobs` output to.
mstarget = 'target_K.ms'                                            # MS file of the target.
myimage = 'target_K_image'                                          # Image.
mycube = 'target_K_cube'                                            # Cube.
mycontsub = 'target_K.ms.contsub'                                   # Continuum subtraction.
skymodel = 'target_K.model'                                         # Sky model.
mymask = 'target_K.mask'                                            # Mask.
myrefant = 'ea05'                                                   # Reference antenna.

##############################################################
# DO NOT EDIT BELOW THIS LINE // DO NOT EDIT BELOW THIS LINE #
##############################################################

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
#Calibration steps
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
                11: 'Clean and self-calibrate (phase) full dataset (clean)',
                12: 'Continuium substraction (uvcontsub)',
                13: 'Make dirty image cube (clean)'}

try:
    print 'List of steps to be executed ...', mysteps
    thesteps = mysteps
except:'
    while 1:
        temp  = raw_input('Variable `mysteps` not set. Execute all steps? (y/n)').lower()
        if temp == 'n':
            sys.exit(0)
        elif temp == 'y':
            thesteps = range(0,len(step_title))
            print 'Executing all steps: ', thesteps
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
    else:
        gtables = ['opacity.cal', 'gaincurve.cal']
        gtables2 = ['opacity.cal', 'gaincurve.cal']
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
    setjy(vis=mssplit,field="0",spw="",selectdata=False,timerange="",scan="",intent="",observation="",scalebychan=True,standard="Perley-Butler 2010",model='%s_%s.im'%(flux_calibrator, flux_calibrator_band),modimage=None,
            listmodels=False,fluxdensity=-1,spix=0.0,reffreq="1GHz",polindex=[],rotmeas=0.0,fluxdict={},useephemdir=False,interpolation="nearest",usescratch=True,ismms=None)
# End of step 3.                               #
################################################

####################################
# Step 4: short phase calibration. #
# Calculate calibrations for the phase changing as function of time.
mystep = 4
if (mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate the calibrations using only a few of the central channels for each spectral window such that the response is essentially flat as function of frequency.
    gaincal(vis=mssplit,caltable="intphase.cal",field="0",spw="*:28~36",intent="",selectdata=False,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=2.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables += ['intphase.cal']
# End of step 4.                   #
####################################

########################################
# Step 5: residual delay calibration.  #
# Calculate calibrations for the phase as function of frequency.
mystep = 5
if (mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate calibrations for the delays between antennas.
    gaincal(vis=mssplit,caltable="delays.cal",field="0",spw="*:4~60",intent="",selectdata=False,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="scan",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=2.0,solnorm=False,gaintype="K",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables += ['delays.cal']
# End of step 5.                       #
########################################

#################################
# Step 6: bandpass calibration. #
# Match shape of bandpass to spectrum of object.
mystep = 6
if (mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate calibrations for the bandpass.
    bandpass(vis=mssplit,caltable="bandpass.cal",field="0",spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="scan",refant=myrefant,minblperant=4,minsnr=2.0,solnorm=False,bandtype="B",smodel=[],append=False,fillgaps=0,degamp=3,degphase=3,visnorm=False,maskcenter=0,maskedge=5,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables += ['bandpass.cal']
# End of step 6.                #
#################################

##########################################
# Step 7: phase & ampltiude calibration. #
# Now use the full range of channels except the ones at the edge, because the response drops rapidly here.
mystep = 7
if (mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Calculate phase calibrations for the flux calibrator.
    gaincal(vis=mssplit,caltable="gainphase.cal",field="0",spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)

    # Calculate phase calibrations for the phase reference (Note `append=True`).
    gaincal(vis=mssplit,caltable="gainphase.cal",field="1",spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=True,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables += ['gainphase.cal']

    # Calculate amplitude calibrations for the flux calibrator.
    gaincal(vis=mssplit,caltable="gainamp.cal",field="0",spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="ap",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=['', '', '', '0', '0', '0'],interp=[],spwmap=[],parang=False)

    # Calculate amplitude calibrations for the phase reference (Note `append=True`).
    gaincal(vis=mssplit,caltable="gainamp.cal",field="1",spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="ap",append=True,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables,gainfield=['', '', '', '0', '0', '1'],interp=[],spwmap=[],parang=False)
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
    flux = fluxscale(vis=mssplit,caltable="gainamp.cal",fluxtable="flux.cal",reference=['0'],transfer=['1'],listfile="",append=False,refspwmap=[-1],gainthreshold=-1.0,antenna="",timerange="",scan="",incremental=True,fitorder=1,display=True)

    setjy(vis=mssplit,field="1",spw="",selectdata=False,timerange="",scan="",intent="",observation="",scalebychan=True,standard="fluxscale",model="",modimage=None,listmodels=False,fluxdensity=-1,spix=0.0,reffreq="1GHz",polindex=[],polangle=[],rotmeas=0.0,fluxdict=flux,useephemdir=False,interpolation="nearest",usescratch=True,ismms=None)

    gaincal(vis=mssplit,caltable="intphase2.cal",field="1",spw="*:28~36",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['intphase2.cal']

    gaincal(vis=mssplit,caltable="delays2.cal",field="1",spw="*:28~36",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="scan",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="K",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['delays2.cal']

    bandpass(vis=mssplit,caltable="bandpass2.cal",field="1",spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="inf",combine="scan",refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,bandtype="B",smodel=[],append=False,fillgaps=0,degamp=3,degphase=3,visnorm=False,maskcenter=0,maskedge=5,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['bandpass2.cal']

    gaincal(vis=mssplit,caltable="gainphase2.cal",field="1",spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="p",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
    gtables2 += ['gainphase2.cal']

    gaincal(vis=mssplit,caltable="gainamp2.cal",field="1",spw="*:4~60",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",solint="int",combine="",preavg=-1.0,refant=myrefant,minblperant=4,minsnr=3.0,solnorm=False,gaintype="G",smodel=[],calmode="ap",append=False,splinetime=3600.0,npointaver=3,phasewrap=180.0,docallib=False,callib="",gaintable=gtables2,gainfield=[],interp=[],spwmap=[],parang=False)
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
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    # Apply calibrations to the flux calibrator.
    applycal(vis=mssplit,field="0",spw="",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",docallib=False,callib="",gaintable=['gaincurve.cal', 'opacity.cal', 'antpos.cal', 'delays.cal', 'bandpass.cal', 'gainphase.cal', 'flux.cal'],gainfield=['', '', '', '0', '0', '0', '0'],interp=['linear', 'linear', 'linear', 'nearest', 'nearest', 'linear', 'nearest'],spwmap=[],calwt=False,parang=False,applymode="",flagbackup=True)

    # Apply calibrations to the phase reference.
    applycal(vis=mssplit,field="1",spw="",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",docallib=False,callib="",gaintable=['gaincurve.cal', 'opacity.cal', 'antpos.cal', 'delays2.cal', 'bandpass2.cal', 'gainphase2.cal', 'gainamp2.cal'],gainfield=['', '', '', '1', '1', '1', '1'],interp=['linear', 'linear', 'linear', 'nearest', 'nearest', 'linear', 'nearest'],spwmap=[],calwt=False,parang=False,applymode="",flagbackup=True)

    # Apply calibrations to the target.
    applycal(vis=mssplit,field="2",spw="",intent="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",msselect="",docallib=False,callib="",gaintable=['gaincurve.cal', 'opacity.cal', 'antpos.cal', 'delays2.cal', 'bandpass2.cal', 'gainphase2.cal', 'gainamp2.cal'],gainfield=['', '', '', '1', '1', '1', '1'],interp=['linear', 'linear', 'linear', 'nearest', 'nearest', 'linear', 'nearest'],spwmap=[],calwt=False,parang=False,applymode="",flagbackup=True)
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
    split(vis=mssplit,outputvis=mstarget,keepmms=True,field="2",spw="",scan="",antenna="",correlation="",timerange="",intent="",array="",uvrange="",observation="",feed="",datacolumn="corrected",keepflags=True,width=1,timebin="0s",combine="")
    split(vis=mssplit,outputvis='phaseref.ms',keepmms=True,field="1",spw="",scan="",antenna="",correlation="",timerange="",intent="",array="",uvrange="",observation="",feed="",datacolumn="corrected",keepflags=True,width=1,timebin="0s",combine="")
    split(vis=mssplit,outputvis='fluxref.ms',keepmms=True,field="0",spw="",scan="",antenna="",correlation="",timerange="",intent="",array="",uvrange="",observation="",feed="",datacolumn="corrected",keepflags=True,width=1,timebin="0s",combine="")
# End of step 10.                #
##################################

####################################################
# Step 11: Create a dirty image and/or dirty cube. #
mystep = 11
if(mystep in thesteps):
    casalog.post('Step '+str(mystep)+' '+step_title[mystep],'INFO')
    print 'Step ', mystep, step_title[mystep]
    clean(vis=mstarget,imagename=mycube,outlierfile="",field="",spw="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",intent="",mode="frequency",resmooth=False,gridmode="",wprojplanes=-1,facets=1,cfcache="cfcache.dir",rotpainc=5.0,painc=360.0,aterm=True,psterm=False,mterm=True,wbawp=False,conjbeams=True,epjtable="",interpolation="linear",niter=0,gain=0.05,threshold="6.0e-5Jy",psfmode="clark",imagermode="csclean",ftmachine="mosaic",mosweight=False,scaletype="SAULT",multiscale=[],negcomponent=-1,smallscalebias=0.6,interactive=False,mask="",nchan=-1,start='22.6794GHz',width='2MHz',outframe="",veltype="radio",imsize=512,cell='0.08arcsec',phasecenter="",restfreq="23.38348GHz",stokes="I",weighting="natural",robust=0,uvtaper=False,outertaper=[''],innertaper=['1.0'],modelimage="",restoringbeam=[''],pbcor=False,minpb=0.2,usescratch=True,noise="1.0Jy",npixels=0,npercycle=100,cyclefactor=1.5,cyclespeedup=-1,nterms=1,reffreq="",chaniter=False,flatnoise=True,allowchunk=False)

    clean(vis='phaseref.ms',imagename='phaseref_cube.ms',outlierfile="",field="",spw="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",intent="",mode="frequency",resmooth=False,gridmode="",wprojplanes=-1,facets=1,cfcache="cfcache.dir",rotpainc=5.0,painc=360.0,aterm=True,psterm=False,mterm=True,wbawp=False,conjbeams=True,epjtable="",interpolation="linear",niter=0,gain=0.05,threshold="6.0e-5Jy",psfmode="clark",imagermode="csclean",ftmachine="mosaic",mosweight=False,scaletype="SAULT",multiscale=[],negcomponent=-1,smallscalebias=0.6,interactive=False,mask="",nchan=-1,start='22.6794GHz',width='2MHz',outframe="",veltype="radio",imsize=256,cell='0.08arcsec',phasecenter="",restfreq="23.38348GHz",stokes="I",weighting="natural",robust=0,uvtaper=False,outertaper=[''],innertaper=['1.0'],modelimage="",restoringbeam=[''],pbcor=False,minpb=0.2,usescratch=True,noise="1.0Jy",npixels=0,npercycle=100,cyclefactor=1.5,cyclespeedup=-1,nterms=1,reffreq="",chaniter=False,flatnoise=True,allowchunk=False)

    clean(vis='fluxref.ms',imagename='fluxref_cube.ms',outlierfile="",field="",spw="",selectdata=True,timerange="",uvrange="",antenna="",scan="",observation="",intent="",mode="frequency",resmooth=False,gridmode="",wprojplanes=-1,facets=1,cfcache="cfcache.dir",rotpainc=5.0,painc=360.0,aterm=True,psterm=False,mterm=True,wbawp=False,conjbeams=True,epjtable="",interpolation="linear",niter=0,gain=0.05,threshold="6.0e-5Jy",psfmode="clark",imagermode="csclean",ftmachine="mosaic",mosweight=False,scaletype="SAULT",multiscale=[],negcomponent=-1,smallscalebias=0.6,interactive=False,mask="",nchan=-1,start='22.6794GHz',width='2MHz',outframe="",veltype="radio",imsize=256,cell='0.08arcsec',phasecenter="",restfreq="23.38348GHz",stokes="I",weighting="natural",robust=0,uvtaper=False,outertaper=[''],innertaper=['1.0'],modelimage="",restoringbeam=[''],pbcor=False,minpb=0.2,usescratch=True,noise="1.0Jy",npixels=0,npercycle=100,cyclefactor=1.5,cyclespeedup=-1,nterms=1,reffreq="",chaniter=False,flatnoise=True,allowchunk=False)
# End of step 11.                #
##################################

####################################################
# Step 12: Create 0th moment map. #
mystep = 12
if (mystep in thesteps):
    immoments(imagename=mstarget+'.image',moments=[0],axis="spectral",region="",box="",chans="340~360",stokes="I",mask=[],includepix=-1,excludepix=-1,outfile="target_CO_mom0_tight",stretch=False)
# End of step 12.                #
##################################
