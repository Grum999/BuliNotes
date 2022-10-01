# -----------------------------------------------------------------------------
# Buli Notes
# Copyright (C) 2021-2022 - Grum999
# -----------------------------------------------------------------------------
# SPDX-License-Identifier: GPL-3.0-or-later
#
# https://spdx.org/licenses/GPL-3.0-or-later.html
# -----------------------------------------------------------------------------
# A Krita plugin designed to manage notes
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# The bnuidocker module provides classes used to manage plugin docker interface
#
# Main classes from this module
#
# - BNUiDocker:
#       Main plugin docker user interface
#
# -----------------------------------------------------------------------------

import os.path

from PyQt5.Qt import *
from PyQt5.QtWidgets import (
        QWidget
    )

from bulinotes.pktk.modules.about import AboutWindow
from bulinotes.pktk.modules.uitheme import UITheme
from bulinotes.pktk.modules.utils import loadXmlUi

from .bnsettings import BNSettings
from .bnnotes import (BNNote,
                      BNNotes,
                      BNNoteEditor
                      )
from .bnwnotes import BNNotesModel
from .bnnote_postit import BNNotePostIt


class BNUiDocker(QWidget):
    """Current selection interface"""

    def __init__(self, docker, bnName="Buli Notes", bnId='', bnVersion="testing", parent=None):
        super(BNUiDocker, self).__init__(parent)
        self.__bnName = bnName
        self.__bnId = bnId
        self.__bnVersion = bnVersion
        self.__docker = docker
        BNSettings.load()
        UITheme.load()
        UITheme.load(os.path.join(os.path.dirname(__file__), 'resources'))
        self.__notes = BNNotes()
        self.__docker = docker

        # on which plugin is currently working on
        self.__kraActiveDocument = None

        self.__notes.updateAdded.connect(self.__updateUi)
        self.__notes.updateRemoved.connect(self.__updateUi)

        uiFileName = os.path.join(os.path.dirname(__file__), 'resources', 'bnuidocker.ui')
        loadXmlUi(uiFileName, self)

        self.__initialize()

    def __initialize(self):
        """Initialise interface"""
        self.tvNotes.setNotes(self.__notes)
        self.tvNotes.selectionModel().selectionChanged.connect(self.__selectionChanged)

        self.tvNotes.doubleClicked.connect(self.__editNote)

        self.btAbout.clicked.connect(self.__about)
        self.btAddNote.clicked.connect(self.__addNote)
        self.btEditNote.clicked.connect(self.__editNote)
        self.btRemoveNote.clicked.connect(self.__removeNote)
        self.btMoveNoteUp.clicked.connect(self.__moveNoteUp)
        self.btMoveNoteDown.clicked.connect(self.__moveNoteDown)
        self.__updateUi()

    def __about(self):
        """Display About window"""
        AboutWindow(self.__bnName, self.__bnVersion, os.path.join(os.path.dirname(__file__), 'resources', 'png', 'buli-powered-big.png'), None, ':BuliNotes')

    def __addNote(self):
        """Add a new note in notes"""
        note = BNNoteEditor.edit(BNNote())
        if note:
            note.setPosition(self.__notes.length())
            self.__notes.add(note)

    def __removeNote(self):
        """Remove selected note from notes"""
        self.__notes.remove(self.tvNotes.selectedItems())

    def __editNote(self, index=None):
        """Edit selected note"""
        if isinstance(index, QModelIndex) and not index.column() in (BNNotesModel.COLNUM_COLOR, BNNotesModel.COLNUM_TITLE):
            # a double-click not made in valid columns does nothing
            return

        selectedItem = self.tvNotes.selectedItems()
        if not selectedItem[0].locked():
            BNNoteEditor.edit(selectedItem[0])
        else:
            if selectedItem[0].windowPostIt():
                selectedItem[0].closeWindowPostIt()
            else:
                selectedItem[0].openWindowPostIt(True)

    def __selectionChanged(self, selected, deselected):
        """Selection in treeview has changed, update UI"""
        self.__updateUi()

    def __updateUi(self):
        """Update current ui according to current selection and document"""
        selectedItems = self.tvNotes.selectedItems()
        nbSelectedItems = len(selectedItems)

        self.btAddNote.setEnabled(not(self.__kraActiveDocument is None))
        self.btEditNote.setEnabled(nbSelectedItems == 1 and not selectedItems[0] is None and not selectedItems[0].locked())
        self.btRemoveNote.setEnabled(nbSelectedItems > 1 or nbSelectedItems == 1 and not selectedItems[0] is None and not selectedItems[0].locked())
        self.btMoveNoteUp.setEnabled(nbSelectedItems > 0 and not selectedItems[0] is None and selectedItems[0].position() > 0)
        self.btMoveNoteDown.setEnabled(nbSelectedItems > 0 and not selectedItems[-1] is None and (selectedItems[-1].position() < self.__notes.length()-1))

        if self.__notes.length() > 0:
            self.__docker.setWindowTitle(f'{self.__bnName} ({self.__notes.length()})')
        else:
            self.__docker.setWindowTitle(self.__bnName)

    def __moveNoteUp(self):
        """Move all selected notes up"""
        self.__notes.movePositionUp(self.tvNotes.selectedItems())

    def __moveNoteDown(self):
        """Move all selected notes down"""
        self.__notes.movePositionDown(self.tvNotes.selectedItems())

    def canvasChanged(self, canvas):
        if canvas and Krita.instance().activeDocument():
            # memorize current document
            self.__kraActiveDocument = canvas.view().document()
        else:
            # no canvas means no document opened
            self.__kraActiveDocument = None
        self.__notes.setDocument(self.__kraActiveDocument)
        self.__updateUi()
