ECHO10_CONSTRUCTION = ${PWD}/echo10-construction/src/
export PYTHONPATH = ${ECHO10_CONSTRUCTION}
export CONFIG = "{}"

test_file ?= tests/
pytest:
	pytest $(test_file)
