#!/bin/bash

cd $PHYSICS_TOP/trace/trace

pydm main.py "$@" &
