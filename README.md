# Buli Notes

A plugin for [Krita](https://krita.org).


## What is Buli Notes?
*Buli Notes* is a Python plugin made for [Krita](https://krita.org) (free professional and open-source painting program).


It allows to add notes to Krita documents.
As notes are embedded into *.kra* file, you're sure to never loose them :-)



## Screenshots

*A screenshot of Krita with* Buli Notes *docker and a note displayed as post-it*

![Pinned note on interface](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-1-0a_fullscreen_example-text.jpg)

| *Hand written informations post-it* | *Brushes list post-it* |
|---|---|
| ![Handwritten note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-1-0a_fullscreen_example-handwritten.jpg) | ![Brushes note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-1-0a_fullscreen_example-brushes.jpg) |
| ***Linked layers informations post-it*** |  |
| ![Linked layers note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_fullscreen_example-linked_layers.jpg) |  |


*Editor - Text note*

![Text note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-1-0a_edit_note-text.jpg)

*Editor - Hand written note*

![Handwritten note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-1-0a_edit_note-handwritten.jpg)


*Editor - Brushes note*

![Handwritten note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-1-0a_edit_note-brushes.jpg)

*Editor - Linked layers note*

![Linked layers note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_edit_note-linked_layers.jpg)



## Functionalities

### Note management
All notes are available through a docker:
- List all defined notes
- Allows to add/edit/remove notes
- Lock/unlock notes
  - A locked note can't be edited/deleted
- Pin/unpin notes
  - By default an opened note is automatically closed when focus is lost; when pinned, note have to be explicitely closed
  - Pinned notes stay visibles in fullscreen mode
- Right click on list allows to copy/paste selected notes from document to another one.

As a post-it, a note can be moved/resized on desktop.


### Notes properties

Notes have the following properties:
- A Title
- A description
- A color

Also, creation and last modification date/time are automatically set on notes.

### Text content
A note can have an optional text content, that the minimal thing we can expect for a note :-D

Text editor allows rich text content and provides following formatting functions:
- Font family
- Font size
- Text weight (normal, bold)
- Text style (italic, underline, color)
- Text alignment (left, center, right, justified)
- Bullet list

Basic undo/redo and copy/paste actions are available.

### Hand written content

It's possible to set hand written notes on a scratchpad.
Could be interesting to draw small schema to illustrate ideas for example.

Hand written notes allows:
- To draw using all available Krita's preset brushes

  ![Handwritten note brushes](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-1-0a_edit_note-handwritten-brushes.jpg)
- To change brush size
- To change brush color

  ![Handwritten note color](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-1-0a_edit_note-handwritten-color.jpg)
- To reset content

To use scratchpad:
- Left click: draw
- Middle click: pan
- Right click: pick color

> **Note**: undo/redo is not available (and not sure to be able to implement it...)

When a note is displayed as a post-it, clicking on scratchpad will change brush color with picked color.

### Brushes list

Krita allows to manage presets (bundles, tags).
Usefull for general configuration or to organize brushes.

But when start drawing, don't want to manage all of this.
Also, don't want to create a preset for each combination size/opacity used for a specific document.

The brushes list allows you to add the current used brush in list:
- Brush preset
- Size
- Opacity
- Flow
- Blending mode

A description can be associated with brush (allows to easily keep in mind for which type of work the brush has been used)

And as note in saved into Krita file, you can do a break and came back few days or few weeks later to finish your drawing, used brushes will be available immediately!

> **Note:** brush preset is not embedded into Krita document, only reference to brush is saved

When a note is displayed as a post-it, clicking on a brush will change current brush with the selected one.


### Linked layers

Layers can be linked to notes with some rich text anotations.
This can be useful in a note to refer to specifics layers, or just to "group" some related layers.

When a note is displayed as a post-it, clicking on a linked layer will activate it as current layer.




## Download, Install & Execute

### Download
+ **[ZIP ARCHIVE - v0.3.0a](https://github.com/Grum999/BuliNotes/releases/download/0.3.0a/bulinotes.zip)**
+ **[SOURCE](https://github.com/Grum999/BuliNotes)**


### Installation

Plugin installation in [Krita](https://krita.org) is not intuitive and needs some manipulation:

1. Open [Krita](https://krita.org) and go to **Tools** -> **Scripts** -> **Import Python Plugins...** and select the **bulinotes.zip** archive and let the software handle it.
2. Restart [Krita](https://krita.org)
3. To enable *Buli Notes* go to **Settings** -> **Configure Krita...** -> **Python Plugin Manager** and click the checkbox to the left of the field that says **Buli Notes**.
4. Restart [Krita](https://krita.org)


### Execute

*Buli Notes* is available as a docker: go to menu **Settings** -> **Dockers** and select **Buli Notes**.


### Tested platforms
> **Notes:**
> - Plugin is not compatible with Krita 4.x.x; you must have at least Krita 5.x.x
> - As currently Krita 5 is still in pre-alpha version, plugin is in alpha version and as long as Krita 5 won't be available as a stable version, plugin will be provided as alpha version

Plugin has been tested with Krita 5.0.0-prealpha (appimage) on Linux Debian 10.
Plugin hasn't been tested on Windows and MacOs


## Plugin's life

### What's new?

_[2021-04-18] Version 0.3.0a_ [>> Show detailed release content <<](https://github.com/Grum999/BuliNotes/blob/master/releases-notes/RELEASE-0.3.0a.md)
- *Post-it mode* - allows to change linked layers properties
- *Color picker* - improve color picker for text/hand written notes
- *Docker* - add mime type "text/plain" and "text/html" for copy/paste action
- *Docker* - allows to change notes positions in list
- *Settings* - implement global settings
- *Miscellaneous* - improve UI, improve performances, fix bugs


_[2021-04-04] Version 0.2.0a_ [>> Show detailed release content <<](https://github.com/Grum999/BuliNotes/blob/master/releases-notes/RELEASE-0.2.0a.md)
- *Linked layers notes* - implement functionality
- *Text notes* - implement strikethrough & bg colors styles
- *Text notes* - implement shortcuts
- *Hand written notes* - implement brush opacity
- *Hand written notes* - implement import/export
- *Brushes notes* - improve post-it mode

_[2021-03-16] Version 0.1.0a_ [>> Show detailed release content <<](https://github.com/Grum999/BuliNotes/blob/master/releases-notes/RELEASE-0.1.0a.md)
- First implemented/released version




### Bugs

There's some bugs, and many functionalities are not yet implemented (even if buttons are already here :-))


> **Using plugin is currently not recommended except for testing & feedback purpose**


### What’s next?

Some ideas currently in mind:
- Note manager
  - Allow to define notes position in list (currently, sorted by creation order)
  - Export/Import notes
  - Extend clipboad mime type (text + png), allowing to paste information in an editor
- Tasks
  - Implement tasks list note
- Link layers
  - Allow to apply some basics action on linked layers (show/hide all, lock/unlock all)


## License

### *Buli Notes* is released under the GNU General Public License (version 3 or any later version).

*Buli Notes* is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

*Buli Notes* is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should receive a copy of the GNU General Public License along with *Buli Notes*. If not, see <https://www.gnu.org/licenses/>.


Long story short: you're free to download, modify as well as redistribute *Buli Notes* as long as this ability is preserved and you give contributors proper credit. This is the same license under which Krita is released, ensuring compatibility between the two.
