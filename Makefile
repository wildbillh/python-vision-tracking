# If using git bash for Windows, use different scripts folder
# and python as the exe.
ifeq ("$(OS)", "Windows_NT")
	SCRIPTS=Scripts
	PYTHON_EXE=python
else
	SCRIPTS=bin
	PYTHON_EXE=python3
endif

VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/${SCRIPTS}/activate
PYTHON=${VENV_NAME}/${SCRIPTS}/${PYTHON_EXE}

init: venv install

venv: $(VENV_NAME)/${SCRIPTS}/activate

$(VENV_NAME)/${SCRIPTS}/activate:
	test -d $(VENV_NAME) || ${PYTHON_EXE} -m venv $(VENV_NAME)

activate:
	$(VENV_NAME)/${SCRIPTS}/activate

install:
	$(VENV_ACTIVATE) && ${PYTHON} -m pip install --upgrade pip -U pip wheel setuptools
	$(VENV_ACTIVATE) && pip3 install -r requirements.txt

test:
	$(VENV_ACTIVATE) && ${PYTHON} -m unittest discover -s . -p 'test_*.py'


coverage:
	$(VENV_ACTIVATE) && ${PYTHON} -m pytest --cov-config=.coveragerc --cov=app/ tests/*.py
	$(VENV_ACTIVATE) && coverage html && coverage xml

run:
	$(VENV_ACTIVATE) && ${PYTHON} -m app $(ARGS)

profile: 
	$(VENV_ACTIVATE) && ${PYTHON} -m cProfile -o profile.stats -m app $(ARGS)



