#-----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2021 - Grum999
#
# A toolkit to make pykrita plugin coding easier :-)
# -----------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.
# If not, see https://www.gnu.org/licenses/
# -----------------------------------------------------------------------------



# -----------------------------------------------------------------------------
import os
import re

import PyQt5.uic

from PyQt5.Qt import *
from PyQt5.QtWidgets import (
        QDialog
    )

from ..pktk import *
from .edialog import EDialog

# -----------------------------------------------------------------------------
class AboutWindow(EDialog):
    """A generic 'about' window

    ̀ name`:        plugin name, as displayed to user
    ̀ version`:     plugin version
    ̀ image`:       a QImage or a complete path/filename to image to use
    ̀ license`:     text to display for license; if None, default GPL3 license is added
    ̀ sourceCode`:  text to display for source code; if None, none idpslayed; if ':xxxx', links to github Grum999/XXXX repo :-)
    `madeWidth`:   text to display for 'made with'

    Expected image size: 900x574
    """

    def __init__(self, name="XXXX", version="testing", image=None, license=None, sourceCode=None, madeWith=None, parent=None):
        super(AboutWindow, self).__init__(os.path.join(os.path.dirname(__file__), '..', 'resources', 'about.ui'), parent)

        self.setWindowTitle(i18n(f'{name}::About'))
        self.setWindowFlags(Qt.Dialog|Qt.WindowTitleHint)
        self.setWindowFlags(self.windowFlags()&~Qt.WindowMinMaxButtonsHint)
        self.lblName.setText(name)
        self.lblVersion.setText(f'v{version}')

        if not image is None:
            if isinstance(image, QImage):
                self.lblImg.setPixmap(QPixmap.fromImage(image))
            elif isinstance(image, str):
                # path/filename to image
                self.lblImg.setPixmap(QPixmap.fromImage(QImage(image)))

        if not madeWith is None:
            self.lblMadeWith.setText(madeWith)

        licenseAndSource=''

        if not license is None:
            licenseAndSource=license
        else:
            licenseAndSource=f'<p>{name} is released under the <a href="https://www.gnu.org/licenses/gpl-3.0.html">GNU General Public License (version 3 or any later version)</a></p>'

        if not sourceCode is None:
            if re.match(':', sourceCode):
                licenseAndSource+=f'<p>Get source code on <a href="https://github.com/Grum999/{sourceCode[1:]}">github/{sourceCode[1:]}</a></p>'
            else:
                licenseAndSource+=sourceCode

        self.lblLicenseAndSource.setText(licenseAndSource)

        self.dbbxOk.accepted.connect(self.close)

        self.exec_()
