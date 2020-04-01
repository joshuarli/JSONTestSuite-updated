#!/usr/bin/env python2

import json
import sys

path = sys.argv[1]
with open(path, "r") as f:
    data = f.read()
    try:
        json.loads(data)
    except Exception as e:
        sys.exit(1)
