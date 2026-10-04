#!/usr/bin/env python3
"""Stage ingest. See README for options."""
import sys
from p2prov.cli import main
main(["ingest"] + sys.argv[1:])
