# Buli Notes :: Release 0.2.0a [2021-04-04]




## Implement Linked Layers

Layers can be linked to note with some optional rich text annotation.

![Linked layers note](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_edit_note-linked_layers.jpg)


This can be useful in a note to be able to make reference to specifics layers, especially when document contains many layers.

Also it could be just useful to virtually "group" some related layers that can't be physically grouped.


### Linked layer editor

A dedicated editor allows to add a layer to a note, or to modify one.

![Linked layers edit](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_edit_note-add_linked_layers.jpg)

It's possible to apply a filter on layer's name, can be useful when document contains a huge number of layers.

### Linked layer post-it

When note is displayed as post-it, linked layers provide layer's name and optional content in the same place; in this case layer's name is displayed as italic within brackets `[ ]`

![Linked layers edit](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_fullscreen_example-linked_layers.jpg)

Clicking on a linked layer will activate it as current layer.


> **Notes:**
> - If a linked layer is renamed in document, no problem, note will still be linked to layer!
> - If a linked layer is deleted in document, note will still be linked to deleted layer: in this case deleted layers will be displayed with warning icon and stripped background
>
>![Linked layers edit](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_fullscreen_example-linked_layers-notfound.jpg)



## Improve text notes

### Styles

New styles have been implemented to text editor:
- Strikethrough
- Background color

![Linked layers edit](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_edit_note-text-new_styles.jpg)


### Shortcuts

Following shortcuts have been added to text editor:

- <kbd>CTRL</kbd>+<kbd>B</kbd> Bold
- <kbd>CTRL</kbd>+<kbd>I</kbd> Italic
- <kbd>CTRL</kbd>+<kbd>U</kbd> Underline
- <kbd>CTRL</kbd>+<kbd>T</kbd> Strikethrough



## Improve hand written notes

### Brush opacity  

It's now possible to change brush opacity when drawing note.

![Linked layers edit](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_edit_note-handwritten-brush_opacity.jpg)


### Import/Export

Hand written note can be created from scratch, or from an image.

Import can be made from:
- An image file (JPEG/PNG)
- Clipboard (if any image data are available in clipboard)
- Current document
- A layer from current document


Hand written note can be exported to:
- An image file (JPEG/PNG)
- Clipboard
- A new layer


## Improve brushes notes

Basic brush properties (name, size and blending mode) are now displayed.

![Linked layers edit](https://github.com/Grum999/BuliNotes/raw/main/screenshots/r0-2-0a_fullscreen_example-brushes_properties.jpg)
