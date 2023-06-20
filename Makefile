run:
	env DISABLE_QT5_COMPAT=1 anki -p Test

build: prepare
	(cd src && zip -r ../dist/lifedrain21.zip * -x "*.pyc" -x "meta.json")

prepare:
	mkdir -p dist
	rm -rf dist/lifedrain21.zip
	find src -name __pycache__ -type d -exec rm -r {} +
