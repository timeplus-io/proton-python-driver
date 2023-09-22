
build:
	python3 -m pip install --upgrade build
	python3 -m build

test:
	pip install ./dist/timeplus-proton-driver-0.2.7.tar.gz