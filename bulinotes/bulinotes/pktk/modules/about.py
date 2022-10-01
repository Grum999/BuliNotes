# -----------------------------------------------------------------------------
# PyKritaToolKit
# Copyright (C) 2019-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# A Krita plugin framework
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The about module provides a generic "About" dialog box
#
# Main class from this module
#
# - AboutWindow:
#       A generic "About" dialog box
#
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
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMinMaxButtonsHint)
        self.lblName.setText(name)
        self.lblVersion.setText(f'v{version}')

        if image is not None:
            if isinstance(image, QImage):
                self.lblImg.setPixmap(QPixmap.fromImage(image))
            elif isinstance(image, str):
                # path/filename to image
                self.lblImg.setPixmap(QPixmap.fromImage(QImage(image)))

        if madeWith is not None:
            self.lblMadeWith.setText(madeWith)

        licenseAndSource = ''

        if license is not None:
            licenseAndSource = license
        else:
            licenseAndSource = f'<p>{name} is released under the <a href="https://www.gnu.org/licenses/gpl-3.0.html">'\
                               f'GNU General Public License (version 3 or any later version)</a></p>'

        if sourceCode is not None:
            if re.match(':', sourceCode):
                licenseAndSource += f'<p>Get source code on <a href="https://github.com/Grum999/{sourceCode[1:]}">github/{sourceCode[1:]}</a></p>'
            else:
                licenseAndSource += sourceCode

        self.lblLicenseAndSource.setText(licenseAndSource)

        self.dbbxOk.accepted.connect(self.close)

        self.exec_()
