all: prepare build

prepare:
	rm -rf dist/*
	find lifedrain -name __pycache__ -type d -exec rm -r {} +
	mkdir -p dist

build:
	(cd lifedrain && zip -r ../dist/lifedrain21.zip * -x "*.pyc")
