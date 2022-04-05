#!/bin/bash

[ ! -e env ] && python3 -m virtualenv env
. ./env/bin/activate || . ./env/Scripts/activate
pip install codecov
codecov
