# -*- coding: utf-8 -*-
'''Paperdoll editor project package.

This package should be usable as a library by other PyQt applications.
'''

__version__ = "0.1.1"

# --------------------------------------------------------------------------- #
# Import libraries
# --------------------------------------------------------------------------- #
import logging
import os
import sys

# add the current working directory to the python path
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)

import simplesignals as sisi


# --------------------------------------------------------------------------- #
# Declare package globals
# --------------------------------------------------------------------------- #
import model
import view
log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Define functions
# --------------------------------------------------------------------------- #
def main():
    # set up logging
    logging.basicConfig(level=logging.INFO)
    log.info("")
    log.info("")
    log.info("Paperdoll editor")
    log.info("")
    log.info("cwd %s", os.getcwd())
    # initialize signalling
    sisi.add_signals("doll drawn", "draw doll", "export doll",
                     "set state", "set style", "state changed",
                     "update dial state")
    sisi.add_channels("editor")
    # create editor model
    model.editor = model.MPaperdollEditor()
    # create Qt GUI
    view.version = __version__
    view.app = view.Application(sys.argv)
    view.gui = view.VEditorWindow(model.editor)
    # display the gui
    log.info("Show main window")
    view.gui.resizeToScreen(width=0.5, height=0.8)
    view.gui.centerOnScreen()
    view.gui.show()
    # draw the doll and define initial state
    for dial in model.editor.dials.values():
        dial.change_value(dial.value + 1)
        dial.change_value(dial.value - 1)
#    print_state()
    # show GUI with Qt
    sys.exit(view.app.exec_())

def print_state():
    print("editor state:")
    for animname, animstate in sorted(model.editor.state.items()):
        print("  ", animname, animstate)
    print("\nview state:")
    for slidername, slider in sorted(view.gui.sliders.sliders.items()):
        print("  ", slidername, slider.value())
