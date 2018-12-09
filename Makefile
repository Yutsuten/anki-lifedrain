all: prepare build

prepare:
	rm -f dist/*
	find src -name __pycache__ -type d -exec rm -r {} +
	mkdir -p dist/

build: build20 build21

build20:
	(cd src && zip -r ../dist/lifedrain_20.zip * -x "*.pyc")

build21:
	(cd src/lifedrain && zip -r ../../dist/lifedrain_21.zip * -x "*.pyc")
