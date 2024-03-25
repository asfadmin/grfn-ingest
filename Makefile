METADATA_CONSTRUCTION = ${PWD}/metadata-construction/src/
VERIFY = ${PWD}/verify/src/
export PYTHONPATH = ${METADATA_CONSTRUCTION}:${VERIFY}
export CONFIG = "{}"

test_file ?= tests/
pytest:
	pytest $(test_file)
