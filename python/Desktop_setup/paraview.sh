#!/bin/bash
module load profile/advanced 
module load autoload VirtualGL
module load autoload ParaView

vglrun -d :0.$((RANDOM%2+1)) paraview
