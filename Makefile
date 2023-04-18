ECHO10_CONSTRUCTION = ${PWD}/echo10-construction/src/
VERIFY = ${PWD}/verify/src/
export PYTHONPATH = ${ECHO10_CONSTRUCTION}:${VERIFY}
export CONFIG = "{}"

test_file ?= tests/
pytest:
	pytest $(test_file)
