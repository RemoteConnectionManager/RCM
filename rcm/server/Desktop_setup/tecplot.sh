#!/bin/bash
shopt -s expand_aliases
module load profile/advanced 
module load autoload VirtualGL
module load tecplot/2012R1
vglrun tec360 $@
