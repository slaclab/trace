#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")/trace/"

usage(){
    pydm main.py --help
}
exit_abnormal(){
    usage
    exit 1
}

MACROS=""
ARGS=""

while [ $# -gt 0 ]
do
    case $1 in
        -m | --macros) MACROS="$2"
                       shift ;;
        *) ARGS+="$1 " ;;
    esac
    shift
done

pydm --hide-nav-bar --hide-status-bar \
    -m "$MACROS" \
    main.py "$ARGS"

exit 0
