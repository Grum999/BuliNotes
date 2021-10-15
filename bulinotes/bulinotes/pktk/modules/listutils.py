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
# List utility: miscellaneous
# -----------------------------------------------------------------------------


def flatten(items):
    """Return a flatten list whatever the number of nested level the list have

    f=flatten([1,2,[3,4],[5,[6,7],[8,[9,10]]]])

    f: [1,2,3,4,5,6,7,8,9,10]
    """
    returned=[]
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
    shiftValue=shiftValue%len(items)
    if shiftValue==0:
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
    returned=[]
    for item in items:
        if not item in returned:
            returned.append(item)
    return returned
