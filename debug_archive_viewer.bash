#!/bin/bash

cd "$(dirname "${BASH_SOURCE[0]}")/archive_viewer/"

usage(){
    echo "PyDM Archive Viewer"
    echo "Usage:" 1>&2
    echo "  launch_archive_viewer.bash" 1>&2
}
exit_abnormal(){
    usage
    exit 1
}

python -m debugpy --listen lcls-dev3:29247 --wait-for-client \
    `which pydm` archive_viewer.py

exit 0
