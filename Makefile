.PHONY: build-dataclasses build-services build install-requirements run

build: install-requirements build-dataclasses build-services

install-requirements:
	python3 -m pip install -r requirements.txt

build-dataclasses:
	python3 -m parsers.json_to_dataclass

build-services:
	python3 -m parsers.json_to_service

run: 
	python3 -m app.main