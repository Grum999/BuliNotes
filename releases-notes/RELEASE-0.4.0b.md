# Buli Notes :: Release 0.4.0b [2021-10-24]


## Embedded fonts

In note editor, it's possible to embed fonts used in document.

Interface provides:
- List of used fonts
- Status of fonts
  - Embbeded
  - Embbedable
  - Not available (note is used in document, but not available on current system and hasn't been embedded)
- Selected font informations (license, file, ...)

![Linked layers note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-4-0b_edit_note-embeddedfonts.jpg)


When a note contains embedded font(s):
- A *f* symbol is indicated in notes list
- Tooltip indicates number of embedded fonts
![Linked layers note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-4-0b_docker-embeddedfonts.jpg)


## Fix ***Basic-5 Size*** brush

From Krita 5.0.0-beta1, brushes have been renamed (no more underscore)
- Default font **b)_Basic-5_Size** has been replaced by **b) Basic-5 Size**
- Also, as a brush can be unavailable in current environment, manage fallback when trying to retrieve brush preset information of an unknown/unavailable brush
