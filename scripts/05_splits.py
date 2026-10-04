#!/usr/bin/env python3
"""Stage splits. See README for options."""
import sys
from p2prov.cli import main
main(["splits"] + sys.argv[1:])
