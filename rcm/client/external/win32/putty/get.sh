  rm plink* md5sums* 
  wget http://the.earth.li/~sgtatham/putty/0.63/x86/plink.exe
  wget http://the.earth.li/~sgtatham/putty/0.63/md5sums
  md5sum plink.exe 
  grep plink md5sums 
  cp plink.exe ../64bit/bin/PLINK.EXE
  cp plink.exe ../32bit/bin/PLINK.EXE
 
