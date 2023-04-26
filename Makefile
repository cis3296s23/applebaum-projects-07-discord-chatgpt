.PHONY: doc

coverage_report:
	coverage run --source=. -m unittest tests/*.py -v

coverage_html:
	coverage html

coverage: coverage_report coverage_html

test:
	python -m unittest tests/*.py 

doc:
	mkdir -p doc
	python -m pydoc -w src.client src.bot src.log main
	mv *.html doc
