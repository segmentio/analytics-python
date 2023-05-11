#!/bin/sh

cat <<EOF > ./journify/version.py
# this file is generated automatically
VERSION = '$1'
EOF
