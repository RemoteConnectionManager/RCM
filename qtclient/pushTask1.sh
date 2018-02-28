#!/bin/bash

cd $HOME/Cineca/Task1/javaHelloWorld
find . -maxdepth 1 ! -name 'src' -type d -exec rm -rf {} +
cd $HOME/Cineca/Task1/pythonHelloWorld
find . -maxdepth 1 ! -name "helloworld.py" -delete
echo -e "\033[0;31mRemoving unecessary direcories\033[0m"

cd $HOME/Cineca

git add -A -v Task1

echo "Inserire il commmento del commit"
read COM
git commit -m $COM

git push origin master
