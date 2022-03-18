
build:
	python3 -m pip install --upgrade build
	python3 -m build

test:
	pip install ./dist/clickhouse-driver-0.2.4.tar.gz