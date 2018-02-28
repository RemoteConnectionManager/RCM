#!/bin/bash
cd javaHelloWorld
#compile module
javac -verbose -d mods/com.HelloWorld src/com.HelloWorld/module-info.java src/com.HelloWorld/com/HelloWorld/Main.java 

#test module
#java --module-path mods -m com.HelloWorld/com.HelloWorld.Main

#jlink module in a CUSTOM folder
if [ -d "HelloWorldJRE" ];then
	echo -e "\033[0;31mLa cartella esiste già\033[0m"
	rm -rf ./HelloWorldJRE
fi
jlink -v --module-path /home/cineca/Scaricati/jdk-9.0.4/jmods:mods --add-modules com.HelloWorld --output HelloWorldJRE
echo -e "\033[0;32mSuccess!\033[0m"
