#!/bin/bash

cd $HOME/Cineca/Task1

git add $(git ls-files -m)

echo "Inserire il commmento del commit"
read COM
git commit -m $COM

git push origin master
