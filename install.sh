#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Root privileges required.  Please run with sudo."
    exit 1
fi
