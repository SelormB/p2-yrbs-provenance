#!/usr/bin/env python3
"""Stage audit. See README for options."""
import sys
from p2prov.cli import main
main(["audit"] + sys.argv[1:])
