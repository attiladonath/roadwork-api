#!/usr/bin/env bash
SCRIPTPATH=`pwd -P`

export PYTHONDONTWRITEBYTECODE=1

export FLASK_DEBUG=1
export FLASK_APP="$SCRIPTPATH/run.py"
