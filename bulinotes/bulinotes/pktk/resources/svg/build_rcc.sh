#!/bin/sh

# Create qrc files
./build_qrc.py

# Build rcc files
/usr/lib/qt5/bin/rcc --format-version 1 --no-compress --binary -o ./../darktheme_icons.rcc dark_icons.qrc
/usr/lib/qt5/bin/rcc --format-version 1 --no-compress --binary -o ./../lighttheme_icons.rcc light_icons.qrc
