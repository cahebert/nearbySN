sigma2=$3
sigma4=$2
sigma6=$1

maxv=100000

~/Documents/git/hotpants/hotpants \
-tmplim ~/Documents/catchingSN/eimage_00701782-0-r-R22_S11-det094.fits \
-inim 	~/Documents/catchingSN/00699127-0-r-R22_S11-det094_dithered_projected00701782.fits \
-outim 	~/Documents/catchingSN/diaimg_i00699127d_t00701782_medium.fits \
-tu	$maxv \
-iu	$maxv \
-gd  	2200 2700 1500 2000 \
-ng 	3 6 $sigma6 4 $sigma4 2 $sigma2


~/Documents/git/hotpants/hotpants \
-tmplim     ~/Documents/catchingSN/eimage_00701782-0-r-R22_S11-det094.fits \
-inim       ~/Documents/catchingSN/00699127-0-r-R22_S11-det094_dithered_projected00701782.fits \
-outim      ~/Documents/catchingSN/diaimg_i00699127d_t00701782_dense.fits \
-tu	    $maxv \
-iu	    $maxv \
-gd         500 1000 1000 1500 \
-ng         3 6 $sigma6 4 $sigma4 2 $sigma2

