#/bin/bash

ABSPATH=$(cd "$(dirname "$0")"; pwd)

cd ${ABSPATH}/dist/Releases 
mkdir -p RCM.app/Contents/MacOS
cp ${ABSPATH}/dist/Releases/RCM_darwin_64bit RCM.app/Contents/MacOS/RCM
rm ${ABSPATH}/dist/Releases/RCM.dmg 
hdiutil create RCM.dmg -volname "RCM" -fs HFS+ -srcfolder RCM.app
