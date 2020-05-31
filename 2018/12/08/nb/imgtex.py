#! /usr/bin/env python

from IPython.core.magic import (Magics, magics_class,
                                cell_magic)
from IPython.display import SVG, display, Image

import subprocess as sp
import os

@magics_class
class imgtex(Magics):
    @cell_magic
    def latex(self, line, cell):
        p = sp.Popen("imgtex foo.png".split(),
                     stdin=sp.PIPE,
                     stdout=sp.PIPE,
                     encoding='utf8')
        p.stdin.write(cell)
        p.stdin.close()
        buf = os.read(p.stdout.fileno(), 2**32)
        display(Image(data=buf, format='png'))

def load_ipython_extension(ipython):
    ipython.register_magics(imgtex)
