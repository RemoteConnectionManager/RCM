#!/bin/bash
shopt -s expand_aliases
module load profile/advanced 
module load autoload VirtualGL
module load autoload ParaView

vglrun  paraview $@
