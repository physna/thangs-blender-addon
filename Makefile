
build-package:
	rm thangs-blender-addon.zip | true
	rm -rf ./.build
	mkdir -p ./.build/thangs-blender-addon
	rsync -Rr --exclude ''.build'' . ./.build/thangs-blender-addon
	cd ./.build && zip -r thangs-blender-addon.zip . -x@thangs-blender-addon/exclude.lst

build-package-staging:
	\cp staging_config.ini config.ini
	make build-package
	git checkout config.ini

build-package-dev:
	\cp dev_config.ini config.ini
	make build-package
	git checkout config.ini

