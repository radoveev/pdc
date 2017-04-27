# -*- coding: utf-8 -*-
'''Launcher module of cuteimp

Start your Qt program from here.
'''


# --------------------------------------------------------------------------- #
# Import libraries
# --------------------------------------------------------------------------- #
import os
import os.path
import sys
import importlib
from pathlib import Path


# --------------------------------------------------------------------------- #
# Import python module or package
# --------------------------------------------------------------------------- #
print("cwd", os.getcwd())
print("python path", sys.path)

# append the parent directory of the working directory to the python path
cwd = Path(os.getcwd()).resolve()
sys.path.append(str(cwd.parent))

# append the project directory to the python path
sys.path.append(str(cwd.parent / "paperdoll"))

import paperdoll
paperdoll.main()


#name = "paperdoll"
## append the launch directory to the python path
#sys.path.append(str(Path(os.getcwd()).resolve()))
##os.chdir("..")
## insert the parent directory of the working directory into the python path
#with open("log.txt", "w") as log:
#    log.write("cwd: %s\n" % os.getcwd())
#    log.write("path: %s\n" % sys.path)
#    parentdir = Path(os.getcwd()).parent.resolve()
#    sys.path.insert(0, str(parentdir))
#    log.write("path: %s\n" % sys.path)
## add the package directory to the python path
#pkgpath = Path(parentdir) / name
#if pkgpath.exists():
#    if pkgpath.is_dir():
#        sys.path.append(str(pkgpath))
## perform the import
#pkg = importlib.import_module(name)
## launch the pkg
#pkg.main()
