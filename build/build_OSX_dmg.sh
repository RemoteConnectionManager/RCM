mkdir -p RCM.app/Contents/MacOS
cp RCM RCM.app/Contents/MacOS
hdiutil create RCM.dmg -volname "RCM" -fs HFS+ -srcfolder RCM.app
