coverage_report:
	coverage run --source=. -m unittest tests/*.py -v

coverage_html:
	coverage html

coverage: coverage_report coverage_html

test:
	python -m unittest tests/*.py 