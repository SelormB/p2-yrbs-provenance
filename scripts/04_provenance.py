#!/usr/bin/env python3
"""Stage provenance. See README for options."""
import sys
from p2prov.cli import main
main(["provenance"] + sys.argv[1:])
