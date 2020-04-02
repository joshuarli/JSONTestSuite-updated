#!/usr/bin/env python3

import ujson as json
import sys

path = sys.argv[1]
with open(path, "rb") as f:
    data = f.read()
    try:
        json.loads(data)
    except Exception as e:
        sys.exit(1)
