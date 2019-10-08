all: prepare build cleanup

prepare:
	rm -rf dist/* tmp/*
	find lifedrain -name __pycache__ -type d -exec rm -r {} +
	mkdir -p dist tmp

build: build20 build21

build20:
	echo -n "import lifedrain" > tmp/lifedrain_loader.py
	cp -r lifedrain tmp/lifedrain
	(cd tmp && zip -r ../dist/lifedrain20.zip * -x "*.pyc")

build21:
	(cd lifedrain && zip -r ../dist/lifedrain21.zip * -x "*.pyc")

cleanup:
	rm -rf tmp/*
