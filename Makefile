install:
	pip install -r requirements.txt

test:
	python -m pytest tests


all:
	@python setup.py install
	