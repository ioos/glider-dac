#!/bin/bash
export PYTHONPATH=.
PYTHON=$HOME/.virtualenvs/gliderdac/bin/python
${PYTHON} scripts/rename_deployment.py aoml/SG60920140719T1700 aoml/SG609-20140719T1700
${PYTHON} scripts/rename_deployment.py aoml/SG60920150206T1720 aoml/SG609-20150206T1720
${PYTHON} scripts/rename_deployment.py aoml/SG61020140715T1400 aoml/SG610-20140715T1400
${PYTHON} scripts/rename_deployment.py aoml/SG61020150206T1750 aoml/SG610-20150206T1750
