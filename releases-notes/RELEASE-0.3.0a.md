# Buli Notes :: Release 0.3.0a [2021-XX-XX]


## Improve Post-it mode - Linked Layers

In post-it mode, it's now possible to change linked layer properties by clicking on icon:
- Visibility
- Pinned to timeline
- Lock
- Inherit alpha
- Alpha lock


It’s also possible to quickly change properties of all linked layers in one click.
Like in blender:
- Click on icon, it will switch status ON/OFF for layer
- Maintain mouse button pressed and move down over other layers:
  - If *left* button is pressed, will apply the same status ON/OFF of first clicked layer to other layer(s)
  - If *right* button is pressed, will invert status ON/OFF of layer(s)

![Linked layers properties](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-3-0a_note-multilayer-modif.webm)

## Improve color picker

Color picker for text/hand written notes has been improved:
- Use palette from Krita instead of standard system palette
- Add Monochromatic color helper
- Can display value as percentage
- Review compact mode

All options are available from context menu:

![Linked layers edit](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-3-0a_colorpicker-full_with_ctxmenu.png)

## Improve Docker

The *copy/cut to clipboard* action now manage additional mime types.


### Mime type *text/plain*

This mime type allows to paste a note in basic text editor:
```
╔═══════════════════╤═════════════════════════════════════════════════════════════════════════════╗
║Title              │A testing note                                                               ║
║Description        │A note used for tests                                                        ║
║                   │There's nothing really interesting, except maybe as an example               ║
║Color              │Purple                                                                       ║
╟───────────────────┼─────────────────────────────────────────────────────────────────────────────╢
║Created            │2021-04-11 23:16:48                                                          ║
║Modified           │2021-04-12 00:04:30                                                          ║
╟───────────────────┼─────────────────────────────────────────────────────────────────────────────╢
║Text notes         │Text note                                                                    ║
║                   │This is an example of formatted text note that can be stored into Krita file.║
║                   │                                                                             ║
║                   │Currently, text editor allows to set:                                        ║
║                   │Font familly                                                                 ║
║                   │Font size                                                                    ║
║                   │Font weight (normal or bold)                                                 ║
║                   │Font style (italic, underline, strikethrough, fg/bg color)                   ║
║                   │Simple bullet lists                                                          ║
╟───────────────────┼─────────────────────────────────────────────────────────────────────────────╢
║Hand written notes │874x480                                                                      ║
╟───────────────────┼─────────────────────────────────────────────────────────────────────────────╢
║Brushes notes      │* Test GBLN 01                                                               ║
║                   │     - Blending mode: inverse_subtract                                       ║
║                   │     - Size:          45.00px                                                ║
║                   │     - Opacity:       100.00%                                                ║
║                   │     - Flow:          100.00%                                                ║
║                   │     Experimental brush                                                      ║
║                   │     (Used for background)                                                   ║
║                   │                                                                             ║
║                   │* d) Ink-8 Sumi-e                                                            ║
║                   │     - Blending mode: normal                                                 ║
║                   │     - Size:          60.00px                                                ║
║                   │     - Opacity:       100.00%                                                ║
║                   │     - Flow:          100.00%                                                ║
║                   │     Used to draw shadows                                                    ║
╟───────────────────┼─────────────────────────────────────────────────────────────────────────────╢
║Linked layers notes│* hair                                                                       ║
║                   │     Need some improvment                                                    ║
║                   │     (shape)                                                                 ║
║                   │                                                                             ║
║                   │* hair and droplights                                                        ║
║                   │     Need some improvement                                                   ║
║                   │     (Shape and light effect)                                                ║
║                   │                                                                             ║
║                   │* fce                                                                        ║
║                   │     Left eye need some rework                                               ║
╚═══════════════════╧═════════════════════════════════════════════════════════════════════════════╝
```

### Mime type *text/html*

This mime type allows to paste a note in a word processing software (like LibreOffice):

![Linked layers edit](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-3-0a_copy-html-paste-libreoffice.jpg)

Page layout & style is minimal, but all text formatting defined in note are kept and images are also available in document.


## Implement global settings

Global settings automatically keep user preferences for the following interface item:
- Color picker layout for text editors
- Color picker layout for scratchpad
- Thumbnails size
