# Buli Notes

An plugin for [Krita](https://krita.org).


## What is Buli Notes?
*Buli Notes* is a Python plugin made for [Krita](https://krita.org) (free professional and open-source painting program).


It allows to add notes to Krita documents.



## Screenshots

*A screenshot of Krita with* Buli Notes *docker and a pinned  note*

![Export file list](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r-0-1-0a_fullscreen_example.jpg)

*Editor*

![Export file list](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r-0-1-0a_edit_note.jpg)


## Functionalities

Currently, notes have:
- Title
- Description
- Color
- Text Content

Editor allows to define rich text content (font family, font size, color, style...)

Notes can be resized/moved on screen.

All notes are available from a docker.


## Download, Install & Execute

### Download
+ **ZIP ARCHIVE - v0.0.0 (no release yet available)**
+ **[SOURCE](https://github.com/Grum999/BuliNotes)**


### Installation

Plugin installation in [Krita](https://krita.org) is not intuitive and needs some manipulation:

1. Open [Krita](https://krita.org) and go to **Tools** -> **Scripts** -> **Import Python Plugins...** and select the **bulinotes.zip** archive and let the software handle it.
2. Restart [Krita](https://krita.org)
3. To enable *Buli Notes* go to **Settings** -> **Configure Krita...** -> **Python Plugin Manager** and click the checkbox to the left of the field that says **Buli Notes**.
4. Restart [Krita](https://krita.org)


### Execute

When you want to execute *Buli Notes*, simply go to menu **Settings** -> **Dockers** and select **Buli Notes**.


### Tested platforms
> note: plugin can't work on version 4.x.x
Plugin has been tested with Krita 5.0.0-prealpha (appimage) on Linux Debian 10

Currently don't kwow if plugin works on Windows and MacOs, but as plugin don't use specific OS functionalities and/resources, it should be ok.



## Plugin's life

### What's new?

_[2020-11-13] Version 0.1.0a_
- First implemented/released version
(Release not yet published)



### Bugs

Which software doesn't have any bugs? :)



### What’s next?

Some ideas, don't know if I'll implement them and if implemented, when:
- Add tasks
- Add links to layers
- Add a scratchpad


## License

### *Buli Notes* is released under the GNU General Public License (version 3 or any later version).

*Buli Notes* is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

*Buli Notes* is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should receive a copy of the GNU General Public License along with *Buli Notes*. If not, see <https://www.gnu.org/licenses/>.


Long story short: you're free to download, modify as well as redistribute *Buli Notes* as long as this ability is preserved and you give contributors proper credit. This is the same license under which Krita is released, ensuring compatibility between the two.
