#-----------------------------------------------------------------------------
# Buli Notes
# Copyright (C) 2021 - Grum999
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
# A Krita plugin designed to manage notes
# -----------------------------------------------------------------------------

import os.path

from PyQt5.Qt import *
from PyQt5.QtWidgets import (
        QWidget
    )

from pktk.modules.about import AboutWindow
from pktk.modules.uitheme import UITheme

from .bnutils import loadXmlUi
from .bnnotes import (BNNote,
                      BNNotes,
                      BNNoteEditor,
                      BNNotePostIt
                    )


# signals:
# activeView changed
# no documents


class BNUiDocker(QWidget):
    """Current selection interface"""

    def __init__(self, docker, bnName="Buli Notes", bnId='', bnVersion="testing", parent=None):
        super(BNUiDocker, self).__init__(parent)
        self.__bnName=bnName
        self.__bnId=bnId
        self.__bnVersion=bnVersion
        self.__docker=docker
        self.__uitheme=UITheme(os.path.join(os.path.dirname(__file__), 'resources'))
        self.__notes=BNNotes()
        self.__docker=docker

        # on which plugin is currently working on
        self.__kraActiveDocument=None

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
        self.__updateUi()

    def __about(self):
        """Display About window"""
        AboutWindow(self.__bnName, self.__bnVersion, os.path.join(os.path.dirname(__file__), 'resources', 'png', 'buli-powered-big.png'), None, ':BuliNotes')

    def __addNote(self):
        """Add a new note in notes"""
        note=BNNoteEditor.edit(BNNote())
        if note:
            note.setPosition(self.__notes.length())
            self.__notes.add(note)

    def __removeNote(self):
        """Remove selected note from notes"""
        self.__notes.remove(self.tvNotes.selectedItems())

    def __editNote(self):
        """Edit selected note"""
        selectedItem=self.tvNotes.selectedItems()
        if not selectedItem[0].locked():
            BNNoteEditor.edit(selectedItem[0])
        else:
            if selectedItem[0].windowPostIt():
                selectedItem[0].closeWindowPostIt()
            else:
                selectedItem[0].openWindowPostIt()



    def __selectionChanged(self, selected, deselected):
        """Selection in treeview has changed, update UI"""
        self.__updateUi()

    def __updateUi(self):
        """Update current ui according to current selection and document"""
        selectedItems=self.tvNotes.selectedItems()
        nbSelectedItems=len(selectedItems)

        self.btAddNote.setEnabled(not(self.__kraActiveDocument is None))
        self.btEditNote.setEnabled(nbSelectedItems==1 and not selectedItems[0] is None and not selectedItems[0].locked())
        self.btRemoveNote.setEnabled(nbSelectedItems>0)
        self.btMoveNoteUp.setEnabled(nbSelectedItems>0 and not selectedItems[0] is None and selectedItems[0].position()>0)
        self.btMoveNoteDown.setEnabled(nbSelectedItems>0 and not selectedItems[-1] is None and (selectedItems[-1].position()<self.__notes.length()-1))

        if self.__notes.length() > 0:
            self.__docker.setWindowTitle(f'{self.__bnName} ({self.__notes.length()})')
        else:
            self.__docker.setWindowTitle(self.__bnName)


    def canvasChanged(self, canvas):
        if canvas and Krita.instance().activeDocument():
            # memorize current document
            self.__kraActiveDocument=canvas.view().document()
        else:
            # no canvas means no document opened
            self.__kraActiveDocument=None
        self.__notes.setDocument(self.__kraActiveDocument)
        self.__updateUi()
