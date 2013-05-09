#!/bin/bash
shopt -s expand_aliases
module load profile/advanced 
module load autoload VirtualGL
module load autoload vaa3d
vglrun vaa3d
# module load autoload OpenCV/2.3.1--gnu--4.1.2
# 
# vglrun /cineca/prod/tools/Vaa3d/gnu--4.1.2/bin/vaa3d
