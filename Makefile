all: prepare build

prepare:
	mkdir -p dist
	rm -rf dist/lifedrain21.zip
	find lifedrain -name __pycache__ -type d -exec rm -r {} +

build:
	(cd lifedrain && zip -r ../dist/lifedrain21.zip * -x "*.pyc")
