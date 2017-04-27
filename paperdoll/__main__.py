# -*- coding: utf-8 -*-
'''Paperdoll editor project launch module.
'''

# --------------------------------------------------------------------------- #
# Import libraries
# --------------------------------------------------------------------------- #
import logging
import os
import sys

# add the current working directory to the python path
sys.path.insert(0, os.getcwd())

import paperdoll


# --------------------------------------------------------------------------- #
# Declare module globals
# --------------------------------------------------------------------------- #
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Execute
# --------------------------------------------------------------------------- #
log.info("Launching from __main__")
paperdoll.main()
