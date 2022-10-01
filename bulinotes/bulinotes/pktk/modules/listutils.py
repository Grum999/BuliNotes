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
# The imgutils module provides miscellaneous list functions
#
# -----------------------------------------------------------------------------


def flatten(items):
    """Return a flatten list whatever the number of nested level the list have

    f=flatten([1,2,[3,4],[5,[6,7],[8,[9,10]]]])

    f: [1,2,3,4,5,6,7,8,9,10]
    """
    returned = []
    for item in items:
        if isinstance(item, (list, tuple)):
            returned.extend(flatten(item))
        else:
            returned.append(item)
    return returned


def rotate(items, shiftValue=1):
    """Rotate list

    - Positive `shiftValue` will rotate to right
    - Negative `shiftValue` will rotate to left


    l=[1,2,3,4]

    x=rotate(l, 1)
    x: [4,1,2,3]

    x=rotate(l, -1)
    x: [2,3,4,1]

    """
    shiftValue = shiftValue % len(items)
    if shiftValue == 0:
        # no rotation...
        return items
    # do rotation
    return items[-shiftValue:] + items[:-shiftValue]


def unique(items):
    """Return list of items with duplicate removed

    Initial order list is preserved
    Note: works with non-hashable object
    """
    # a faster method could be return list(set(items))
    # but it doesn't work with non-hashable object (like a QColor for example)
    returned = []
    for item in items:
        if item not in returned:
            returned.append(item)
    return returned
