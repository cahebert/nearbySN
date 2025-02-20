#!/bin/bash

# Want template image (first) to be the *smaller* seeing. 
# Will be convolved to match the "science" image.

# images can be input in any order; measure step determines which is "template"
expid_1=$1
expid_2=$2
pair=$3

datadir="/Users/clairealice/Documents/git/nearbySN/data/p$pair/"
if [ ! -d "$datadir" ]; then
  mkdir $datadir
fi

instf="/Users/clairealice/Documents/git/nearbySN/instcats/instcat_trilegal_p"$pair"_"

# conda init
# conda activate imsim

# # simulate the images!!
# galsim custom-imsim-config.yaml \
#    input.instance_catalog.file_name=$instf$expid_1.txt \
#    output.dir=${datadir} \
#    output.truth.dir=${datadir}

# galsim custom-imsim-config.yaml \
#    input.instance_catalog.file_name=$instf$expid_2.txt \
#    output.dir=${datadir} \
#    output.truth.dir=${datadir}

# # measure sources to get PSF width sigma_match for the differencing
# # this step also determines which image is 'template' vs 'science image'
# output=($(python measure_sources.py --images \
#           $datadir/eimage_$expid_1-0-r-R22_S11-det094.fits \
#           $datadir/eimage_$expid_2-0-r-R22_S11-det094.fits))

# sigma6="${output[0]}"
# sigma4="${output[1]}"
# sigma2="${output[2]}"
# expid_tmp="${output[3]}"
# expid_img="${output[4]}"

# python measure_sources.py --images \
#        $datadir/eimage_$expid_1-0-r-R22_S11-det094.fits \
#        $datadir/eimage_$expid_2-0-r-R22_S11-det094.fits

# sigma2="1.8150782423896967"
# sigma4="0.9075391211948484"
# sigma6="0.4537695605974242"
expid_tmp=$expid_1
expid_img=$expid_2

sigma2="3.6"
sigma4="1.75"
sigma6="0.80"

# wahoo

# python project_images.py --images \
#     $datadir"eimage_$expid_img-0-r-R22_S11-det094.fits" \
#     $datadir"eimage_$expid_tmp-0-r-R22_S11-det094.fits"

maxv=30000

# ~/Documents/git/hotpants/hotpants \
# -tmplim $datadir/eimage_$expid_tmp-0-r-R22_S11-det094.fits \
# -inim   $datadir/eimage_$expid_img-0-r-R22_S11-det094_projected.fits \
# -outim  $datadir/diffim_t$expid_tmp-i$expid_img-low.fits \
# -tu     $maxv \
# -iu     $maxv \
# -gd     2200 2700 1500 2000 \
# -ng     3 6 $sigma6 4 $sigma4 2 $sigma2 \
# -r		16
# -ng     3 6 $sigma6 4 $sigma4 2 $sigma2 \
# -tr 10 -ir 10 \
# -bgo 2
# -nsx 8 -nsy 10 \
# -gd     2000 2200 2000 2200 \

~/Documents/git/hotpants/hotpants \
-tmplim $datadir/eimage_$expid_tmp-0-r-R22_S11-det094_projected_CROPPED.fits \
-inim   $datadir/eimage_$expid_img-0-r-R22_S11-det094_CROPPED.fits \
-outim  $datadir/diffim_t$expid_tmp-i$expid_img.fits \
-ng     3 6 $sigma6 4 $sigma4 2 $sigma2 \
-tu     $maxv \
-iu     $maxv \
-r 		15 \
-n 		t \
-ft 	15 \
-ks 	2.5  \
-v    0 \
-tl   10000 \
-il   10000 \
-nsx  2 \
-nsy  2 

