run:
	anki -p Test

build: prepare
	(cd src && zip -r ../dist/lifedrain.zip * -x "*.pyc" -x "meta.json")

prepare:
	mkdir -p dist
	rm -f dist/lifedrain.zip
	find src -name __pycache__ -type d -exec rm -r {} +
