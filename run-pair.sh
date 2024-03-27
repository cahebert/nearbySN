#!/usr/bin/bash

instcat=$1
outdir=$2
#N=$2

galsim custom-imsim-config.yaml \
   input.instance_catalog.file_name=$instcat \
   output.dir=${outdir} \
   output.truth.dir=${outdir}
