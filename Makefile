
build-package:
	rm -rf ./.build
	mkdir -p ./.build/thangs-blender-addon
	rsync -Rr --exclude ''.build'' . ./.build/thangs-blender-addon
	cd ./.build/thangs-blender-addon
	zip -r thangs-blender-addon.zip . -x@exclude.lst
