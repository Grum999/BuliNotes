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
# The e module provides extended classes and method for Krita
#
# Main classes from this module
#
# - EKritaWindow:
#       Provides methods to access to some Krita mainwindow widgets
#
# - EKritaBrushPreset:
#       Allows 'secured' access to brushes presets
#
# - EKritaShortcuts:
#       Provides methods to manage shortcuts
#
# - EKritaPaintToolsId & EKritaPaintTools:
#       Provides methods for quick access to paint tools
#
# - EKritaBlendingModesId & EKritaBlendingModes:
#       Provides methods for quick access to paint tools
#
# - EKritaDocument:
#       Provides additionals methods to manage documents
#
# - EKritaNode:
#       Provides additionals methods to manage nodes
#
# -----------------------------------------------------------------------------

from enum import Enum
import re

from ..pktk import *
from krita import (
        Document,
        Node,
        Resource
    )

from PyQt5.QtCore import (
        QByteArray,
        QEventLoop,
        QMimeData,
        QPoint,
        QRect,
        QTimer,
        QUuid,
    )
from PyQt5.QtGui import (
        QGuiApplication,
        QKeySequence,
        QImage,
        QPixmap,
        qRgb
    )
from PyQt5.QtWidgets import (
        QWidget,
        QToolButton,
        QListView
    )

from PyQt5.Qt import (QObject, QMdiArea, QAbstractScrollArea)


# -----------------------------------------------------------------------------

class EKritaWindow:

    @staticmethod
    def scrollbars(window=None):
        """Return scrollbar instances of window

        If `window` is None, use active window

        Return a tuple (horizontalScrollBar, verticalScrollBar)
        If there's no active window, return None
        """
        window = Krita.instance().activeWindow()
        if window is None:
            return None

        qtWindow = Krita.instance().activeWindow().qwindow()
        mdiArea = qtWindow.centralWidget().findChild(QMdiArea)
        subWindow = mdiArea.activeSubWindow()
        scrollArea = subWindow.findChild(QAbstractScrollArea)

        return (scrollArea.horizontalScrollBar(), scrollArea.verticalScrollBar())


class EKritaBrushPreset:
    """Allows 'secured' access to brushes preset

    The main cases:
    - Default brush preset used is not availables
    - Brush preset saved (in a plugin) is not available anymore

    In both case, we need to be able to manage properly acces to resources

    The EKritaBrushPreset class provides static methods to acces to brushes in 'secure' way

    There's a third case we won't manage (not a normal case, hope this will be fixed)
        https://krita-artists.org/t/second-beta-for-krita-5-0-help-in-testing-krita/30262/19?u=grum999
    """

    # define some brushes preset we can consider to be used as default
    __DEFAUL_BRUSH_NAMES = ['b) Basic-5 Size',
                            'b) Basic-1',
                            'c) Pencil-2',
                            'd) Ink-2 Fineliner',
                            'd) Ink-3 Gpen'
                            ]

    __brushes = None
    __presetChooserWidget = None

    @staticmethod
    def initialise():
        """Initialise brushes names"""
        EKritaBrushPreset.__brushes = Krita.instance().resources("preset")

    @staticmethod
    def getName(name=None):
        """Return preset name from name

        Given `name` can be a <str> or a <Resource> (preset)

        If brush preset is found, return brush preset name
        Otherwise if can't be found in presets, return the default brush name
        """
        if EKritaBrushPreset.__brushes is None:
            EKritaBrushPreset.initialise()

        if isinstance(name, Resource):
            name = name.name()

        if name in EKritaBrushPreset.__brushes:
            # asked brush found, return it
            return name
        else:
            # asked brush not found, search for a default brush
            for brushName in EKritaBrushPreset.__DEFAUL_BRUSH_NAMES:
                if brushName in EKritaBrushPreset.__brushes:
                    # default brush found, return it
                    return brushName

            # default brush not found :-/
            # return current brush from view
            if Krita.instance().activeWindow() and Krita.instance().activeWindow().activeView():
                brushName = Krita.instance().activeWindow().activeView().currentBrushPreset().name()
            else:
                brushName = None

            if brushName in EKritaBrushPreset.__brushes:
                # asked brush found, return it
                return brushName

            # weird..
            # but can happen!
            # https://krita-artists.org/t/second-beta-for-krita-5-0-help-in-testing-krita/30262/19?u=grum999

            if len(EKritaBrushPreset.__brushes) > 0:
                # return the first one...
                return EKritaBrushPreset.__brushes[list(EKritaBrushPreset.__brushes.keys())[0]].name()

            # this case should never occurs I hope!!
            raise EInvalidStatus(f'Something weird happened!\n'
                                 f'- Given brush name "{name}" was not found\n'
                                 f'- Current brush "{brushName}" returned but Krita doesn\'t exist\n'
                                 f'- Brush preset list returned by Krita is empty\n\nCan\'t do anything...')

    @staticmethod
    def getPreset(name=None):
        """Return preset for given name

        Given `name` can be a <str> or a <Resource> (preset)

        If brush preset is found, return brush preset
        Otherwise if can't be found in presets, return the default brush preset
        """
        if EKritaBrushPreset.__brushes is None:
            EKritaBrushPreset.initialise()

        return EKritaBrushPreset.__brushes[EKritaBrushPreset.getName(name)]

    @staticmethod
    def found(name):
        """Return if brush preset (from name) exists and can be used"""
        return EKritaBrushPreset.getName(name) == name

    @staticmethod
    def presetChooserWidget():
        """Return preset chooser on which 'currentResourceChanged' signal can be
        connected

        EKritaBrushPreset.presetChooserWidget().currentResourceChanged.connect(myFunction)

        Solution provided by @KnowZero on KA
             https://krita-artists.org/t/it-is-sane-for-a-plugin-to-capture-krita-internal-signal/32475/6
        """
        if EKritaBrushPreset.__presetChooserWidget is None:
            window = Krita.instance().activeWindow().qwindow()
            widget = window.findChild(QWidget, 'ResourceChooser')
            EKritaBrushPreset.__presetChooserWidget = widget.findChild(QListView, 'ResourceItemview')

        return EKritaBrushPreset.__presetChooserWidget


class EKritaShortcuts:
    """Manage shortcuts"""

    @staticmethod
    def checkIfExists(keySequence):
        """Check if given `keySequence` is already used by a Krita action

        Return a list of action using the sequence
        """
        returned = []
        actions = Krita.instance().actions()
        for action in actions:
            shortcuts = action.shortcuts()
            for shortcut in shortcuts:
                if keySequence.matches(shortcut) == QKeySequence.ExactMatch:
                    returned.append(action)
                    break
        return returned


class EKritaPaintToolsId:
    """Paint tools Id"""
    TOOL_BRUSH =          'KritaShape/KisToolBrush'
    TOOL_LINE =           'KritaShape/KisToolLine'
    TOOL_RECTANGLE =      'KritaShape/KisToolRectangle'
    TOOL_ELLIPSE =        'KritaShape/KisToolEllipse'
    TOOL_POLYGON =        'KisToolPolygon'
    TOOL_POLYLINE =       'KisToolPolyline'
    TOOL_PATH =           'KritaShape/KisToolPath'
    TOOL_PENCIL =         'KisToolPencil'
    TOOL_DYNAMIC_BRUSH =  'KritaShape/KisToolDyna'
    TOOL_MULTI_BRUSH =    'KritaShape/KisToolMultiBrush'


class EKritaPaintTools:
    """Quick access to paint tools"""

    __TOOLS = {
            EKritaPaintToolsId.TOOL_BRUSH:           i18n("Freehand Brush Tool"),
            EKritaPaintToolsId.TOOL_LINE:            i18n("Line Tool"),
            EKritaPaintToolsId.TOOL_RECTANGLE:       i18n("Rectangle Tool"),
            EKritaPaintToolsId.TOOL_ELLIPSE:         i18n("Ellipse Tool"),
            EKritaPaintToolsId.TOOL_POLYGON:         i18n("Polygon Tool: Shift-mouseclick ends the polygon."),
            EKritaPaintToolsId.TOOL_POLYLINE:        i18n("Polyline Tool: Shift-mouseclick ends the polyline."),
            EKritaPaintToolsId.TOOL_PATH:            i18n("Bezier Curve Tool: Shift-mouseclick ends the curve."),
            EKritaPaintToolsId.TOOL_PENCIL:          i18n("Freehand Path Tool"),
            EKritaPaintToolsId.TOOL_DYNAMIC_BRUSH:   i18n("Dynamic Brush Tool"),
            EKritaPaintToolsId.TOOL_MULTI_BRUSH:     i18n("Multibrush Tool")
        }

    @staticmethod
    def idList():
        """Return list of tools identifiers"""
        return list(EKritaPaintTools.__TOOLS)

    @staticmethod
    def name(id):
        """Return (translated) name for paint tools

        None value return 'None' string

        Otherwise Raise an error is tools is not found
        """
        if id is None:
            return i18n('None')
        elif id in EKritaPaintTools.__TOOLS:
            return re.sub('\s*:.*', '', EKritaPaintTools.__TOOLS[id])
        else:
            raise EInvalidValue("Given `id` is not valid")

    @staticmethod
    def current():
        """return id of current paint tool, if any active

        Otherwise return None
        """
        window = Krita.instance().activeWindow()
        if window:
            for id in EKritaPaintTools.__TOOLS:
                toolButton = window.qwindow().findChild(QToolButton, id)
                if toolButton and toolButton.isChecked():
                    return id
        return None


class EKritaBlendingModesId:
    """Blending modes Id"""
    # list from:
    #   https://invent.kde.org/graphics/krita/-/blob/master/libs/pigment/KoCompositeOpRegistry.h
    COMPOSITE_OVER =                             "normal"
    COMPOSITE_ERASE =                            "erase"
    COMPOSITE_IN =                               "in"
    COMPOSITE_OUT =                              "out"
    COMPOSITE_ALPHA_DARKEN =                     "alphadarken"
    COMPOSITE_DESTINATION_IN =                   "destination-in"
    COMPOSITE_DESTINATION_ATOP =                 "destination-atop"

    COMPOSITE_XOR =                              "xor"
    COMPOSITE_OR =                               "or"
    COMPOSITE_AND =                              "and"
    COMPOSITE_NAND =                             "nand"
    COMPOSITE_NOR =                              "nor"
    COMPOSITE_XNOR =                             "xnor"
    COMPOSITE_IMPLICATION =                      "implication"
    COMPOSITE_NOT_IMPLICATION =                  "not_implication"
    COMPOSITE_CONVERSE =                         "converse"
    COMPOSITE_NOT_CONVERSE =                     "not_converse"

    COMPOSITE_PLUS =                             "plus"
    COMPOSITE_MINUS =                            "minus"
    COMPOSITE_ADD =                              "add"
    COMPOSITE_SUBTRACT =                         "subtract"
    COMPOSITE_INVERSE_SUBTRACT =                 "inverse_subtract"
    COMPOSITE_DIFF =                             "diff"
    COMPOSITE_MULT =                             "multiply"
    COMPOSITE_DIVIDE =                           "divide"
    COMPOSITE_ARC_TANGENT =                      "arc_tangent"
    COMPOSITE_GEOMETRIC_MEAN =                   "geometric_mean"
    COMPOSITE_ADDITIVE_SUBTRACTIVE =             "additive_subtractive"
    COMPOSITE_NEGATION =                         "negation"

    COMPOSITE_MOD =                              "modulo"
    COMPOSITE_MOD_CON =                          "modulo_continuous"
    COMPOSITE_DIVISIVE_MOD =                     "divisive_modulo"
    COMPOSITE_DIVISIVE_MOD_CON =                 "divisive_modulo_continuous"
    COMPOSITE_MODULO_SHIFT =                     "modulo_shift"
    COMPOSITE_MODULO_SHIFT_CON =                 "modulo_shift_continuous"

    COMPOSITE_EQUIVALENCE =                      "equivalence"
    COMPOSITE_ALLANON =                          "allanon"
    COMPOSITE_PARALLEL =                         "parallel"
    COMPOSITE_GRAIN_MERGE =                      "grain_merge"
    COMPOSITE_GRAIN_EXTRACT =                    "grain_extract"
    COMPOSITE_EXCLUSION =                        "exclusion"
    COMPOSITE_HARD_MIX =                         "hard mix"
    COMPOSITE_HARD_MIX_PHOTOSHOP =               "hard_mix_photoshop"
    COMPOSITE_HARD_MIX_SOFTER_PHOTOSHOP =        "hard_mix_softer_photoshop"
    COMPOSITE_OVERLAY =                          "overlay"
    COMPOSITE_BEHIND =                           "behind"
    COMPOSITE_GREATER =                          "greater"
    COMPOSITE_HARD_OVERLAY =                     "hard overlay"
    COMPOSITE_INTERPOLATION =                    "interpolation"
    COMPOSITE_INTERPOLATIONB =                   "interpolation 2x"
    COMPOSITE_PENUMBRAA =                        "penumbra a"
    COMPOSITE_PENUMBRAB =                        "penumbra b"
    COMPOSITE_PENUMBRAC =                        "penumbra c"
    COMPOSITE_PENUMBRAD =                        "penumbra d"

    COMPOSITE_DARKEN =                           "darken"
    COMPOSITE_BURN =                             "burn"          # color burn
    COMPOSITE_LINEAR_BURN =                      "linear_burn"
    COMPOSITE_GAMMA_DARK =                       "gamma_dark"
    COMPOSITE_SHADE_IFS_ILLUSIONS =              "shade_ifs_illusions"
    COMPOSITE_FOG_DARKEN_IFS_ILLUSIONS =         "fog_darken_ifs_illusions"
    COMPOSITE_EASY_BURN =                        "easy burn"

    COMPOSITE_LIGHTEN =                          "lighten"
    COMPOSITE_DODGE =                            "dodge"
    COMPOSITE_LINEAR_DODGE =                     "linear_dodge"
    COMPOSITE_SCREEN =                           "screen"
    COMPOSITE_HARD_LIGHT =                       "hard_light"
    COMPOSITE_SOFT_LIGHT_IFS_ILLUSIONS =         "soft_light_ifs_illusions"
    COMPOSITE_SOFT_LIGHT_PEGTOP_DELPHI =         "soft_light_pegtop_delphi"
    COMPOSITE_SOFT_LIGHT_PHOTOSHOP =             "soft_light"
    COMPOSITE_SOFT_LIGHT_SVG =                   "soft_light_svg"
    COMPOSITE_GAMMA_LIGHT =                      "gamma_light"
    COMPOSITE_GAMMA_ILLUMINATION =               "gamma_illumination"
    COMPOSITE_VIVID_LIGHT =                      "vivid_light"
    COMPOSITE_FLAT_LIGHT =                       "flat_light"
    COMPOSITE_LINEAR_LIGHT =                     "linear light"
    COMPOSITE_PIN_LIGHT =                        "pin_light"
    COMPOSITE_PNORM_A =                          "pnorm_a"
    COMPOSITE_PNORM_B =                          "pnorm_b"
    COMPOSITE_SUPER_LIGHT =                      "super_light"
    COMPOSITE_TINT_IFS_ILLUSIONS =               "tint_ifs_illusions"
    COMPOSITE_FOG_LIGHTEN_IFS_ILLUSIONS =        "fog_lighten_ifs_illusions"
    COMPOSITE_EASY_DODGE =                       "easy dodge"
    COMPOSITE_LUMINOSITY_SAI =                   "luminosity_sai"

    COMPOSITE_HUE =                              "hue"
    COMPOSITE_COLOR =                            "color"
    COMPOSITE_SATURATION =                       "saturation"
    COMPOSITE_INC_SATURATION =                   "inc_saturation"
    COMPOSITE_DEC_SATURATION =                   "dec_saturation"
    COMPOSITE_LUMINIZE =                         "luminize"
    COMPOSITE_INC_LUMINOSITY =                   "inc_luminosity"
    COMPOSITE_DEC_LUMINOSITY =                   "dec_luminosity"

    COMPOSITE_HUE_HSV =                          "hue_hsv"
    COMPOSITE_COLOR_HSV =                        "color_hsv"
    COMPOSITE_SATURATION_HSV =                   "saturation_hsv"
    COMPOSITE_INC_SATURATION_HSV =               "inc_saturation_hsv"
    COMPOSITE_DEC_SATURATION_HSV =               "dec_saturation_hsv"
    COMPOSITE_VALUE =                            "value"
    COMPOSITE_INC_VALUE =                        "inc_value"
    COMPOSITE_DEC_VALUE =                        "dec_value"

    COMPOSITE_HUE_HSL =                          "hue_hsl"
    COMPOSITE_COLOR_HSL =                        "color_hsl"
    COMPOSITE_SATURATION_HSL =                   "saturation_hsl"
    COMPOSITE_INC_SATURATION_HSL =               "inc_saturation_hsl"
    COMPOSITE_DEC_SATURATION_HSL =               "dec_saturation_hsl"
    COMPOSITE_LIGHTNESS =                        "lightness"
    COMPOSITE_INC_LIGHTNESS =                    "inc_lightness"
    COMPOSITE_DEC_LIGHTNESS =                    "dec_lightness"

    COMPOSITE_HUE_HSI =                          "hue_hsi"
    COMPOSITE_COLOR_HSI =                        "color_hsi"
    COMPOSITE_SATURATION_HSI =                   "saturation_hsi"
    COMPOSITE_INC_SATURATION_HSI =               "inc_saturation_hsi"
    COMPOSITE_DEC_SATURATION_HSI =               "dec_saturation_hsi"
    COMPOSITE_INTENSITY =                        "intensity"
    COMPOSITE_INC_INTENSITY =                    "inc_intensity"
    COMPOSITE_DEC_INTENSITY =                    "dec_intensity"

    COMPOSITE_COPY =                             "copy"
    COMPOSITE_COPY_RED =                         "copy_red"
    COMPOSITE_COPY_GREEN =                       "copy_green"
    COMPOSITE_COPY_BLUE =                        "copy_blue"
    COMPOSITE_TANGENT_NORMALMAP =                "tangent_normalmap"

    COMPOSITE_COLORIZE =                         "colorize"
    COMPOSITE_BUMPMAP =                          "bumpmap"
    COMPOSITE_COMBINE_NORMAL =                   "combine_normal"
    COMPOSITE_CLEAR =                            "clear"
    COMPOSITE_DISSOLVE =                         "dissolve"
    COMPOSITE_DISPLACE =                         "displace"
    COMPOSITE_NO =                               "nocomposition"
    COMPOSITE_PASS_THROUGH =                     "pass through"  # XXX: not implemented anywhere yet?
    COMPOSITE_DARKER_COLOR =                     "darker color"
    COMPOSITE_LIGHTER_COLOR =                    "lighter color"
    # COMPOSITE_UNDEF =                            "undefined"

    COMPOSITE_REFLECT =                          "reflect"
    COMPOSITE_GLOW =                             "glow"
    COMPOSITE_FREEZE =                           "freeze"
    COMPOSITE_HEAT =                             "heat"
    COMPOSITE_GLEAT =                            "glow_heat"
    COMPOSITE_HELOW =                            "heat_glow"
    COMPOSITE_REEZE =                            "reflect_freeze"
    COMPOSITE_FRECT =                            "freeze_reflect"
    COMPOSITE_FHYRD =                            "heat_glow_freeze_reflect_hybrid"

    CATEGORY_ARITHMETIC =                        "arithmetic"
    CATEGORY_BINARY =                            "binary"
    CATEGORY_DARK =                              "dark"
    CATEGORY_LIGHT =                             "light"
    CATEGORY_MODULO =                            "modulo"
    CATEGORY_NEGATIVE =                          "negative"
    CATEGORY_MIX =                               "mix"
    CATEGORY_MISC =                              "misc"
    CATEGORY_HSY =                               "hsy"
    CATEGORY_HSI =                               "hsi"
    CATEGORY_HSL =                               "hsl"
    CATEGORY_HSV =                               "hsv"
    CATEGORY_QUADRATIC =                         "quadratic"


class EKritaBlendingModes:
    """Blending modes"""
    # tables & translations from
    #   https://invent.kde.org/graphics/krita/-/blob/master/libs/pigment/KoCompositeOpRegistry.cpp
    __CATEGORIES = {
            EKritaBlendingModesId.CATEGORY_ARITHMETIC:                          i18nc("Blending mode - category Arithmetic", "Arithmetic"),
            EKritaBlendingModesId.CATEGORY_BINARY:                              i18nc("Blending mode - category Binary", "Binary"),
            EKritaBlendingModesId.CATEGORY_DARK:                                i18nc("Blending mode - category Darken", "Darken"),
            EKritaBlendingModesId.CATEGORY_LIGHT:                               i18nc("Blending mode - category Lighten", "Lighten"),
            EKritaBlendingModesId.CATEGORY_MODULO:                              i18nc("Blending mode - category Modulo", "Modulo"),
            EKritaBlendingModesId.CATEGORY_NEGATIVE:                            i18nc("Blending mode - category Negative", "Negative"),
            EKritaBlendingModesId.CATEGORY_MIX:                                 i18nc("Blending mode - category Mix", "Mix"),
            EKritaBlendingModesId.CATEGORY_MISC:                                i18nc("Blending mode - category Misc", "Misc"),
            EKritaBlendingModesId.CATEGORY_HSY:                                 i18nc("Blending mode - category HSY", "HSY"),
            EKritaBlendingModesId.CATEGORY_HSI:                                 i18nc("Blending mode - category HSI", "HSI"),
            EKritaBlendingModesId.CATEGORY_HSL:                                 i18nc("Blending mode - category HSL", "HSL"),
            EKritaBlendingModesId.CATEGORY_HSV:                                 i18nc("Blending mode - category HSV", "HSV"),
            EKritaBlendingModesId.CATEGORY_QUADRATIC:                           i18nc("Blending mode - category Quadratic", "Quadratic")
        }

    __CATEGORIES_BLENDING_MODES = {
            EKritaBlendingModesId.CATEGORY_ARITHMETIC: [
                    EKritaBlendingModesId.COMPOSITE_ADD,
                    EKritaBlendingModesId.COMPOSITE_SUBTRACT,
                    EKritaBlendingModesId.COMPOSITE_MULT,
                    EKritaBlendingModesId.COMPOSITE_DIVIDE,
                    EKritaBlendingModesId.COMPOSITE_INVERSE_SUBTRACT
                ],
            EKritaBlendingModesId.CATEGORY_BINARY: [
                    EKritaBlendingModesId.COMPOSITE_XOR,
                    EKritaBlendingModesId.COMPOSITE_OR,
                    EKritaBlendingModesId.COMPOSITE_AND,
                    EKritaBlendingModesId.COMPOSITE_NAND,
                    EKritaBlendingModesId.COMPOSITE_NOR,
                    EKritaBlendingModesId.COMPOSITE_XNOR,
                    EKritaBlendingModesId.COMPOSITE_IMPLICATION,
                    EKritaBlendingModesId.COMPOSITE_NOT_IMPLICATION,
                    EKritaBlendingModesId.COMPOSITE_CONVERSE,
                    EKritaBlendingModesId.COMPOSITE_NOT_CONVERSE
                ],
            EKritaBlendingModesId.CATEGORY_DARK: [
                    EKritaBlendingModesId.COMPOSITE_BURN,
                    EKritaBlendingModesId.COMPOSITE_LINEAR_BURN,
                    EKritaBlendingModesId.COMPOSITE_DARKEN,
                    EKritaBlendingModesId.COMPOSITE_GAMMA_DARK,
                    EKritaBlendingModesId.COMPOSITE_DARKER_COLOR,
                    EKritaBlendingModesId.COMPOSITE_SHADE_IFS_ILLUSIONS,
                    EKritaBlendingModesId.COMPOSITE_FOG_DARKEN_IFS_ILLUSIONS,
                    EKritaBlendingModesId.COMPOSITE_EASY_BURN
                ],
            EKritaBlendingModesId.CATEGORY_LIGHT: [
                    EKritaBlendingModesId.COMPOSITE_DODGE,
                    EKritaBlendingModesId.COMPOSITE_LINEAR_DODGE,
                    EKritaBlendingModesId.COMPOSITE_LIGHTEN,
                    EKritaBlendingModesId.COMPOSITE_LINEAR_LIGHT,
                    EKritaBlendingModesId.COMPOSITE_SCREEN,
                    EKritaBlendingModesId.COMPOSITE_PIN_LIGHT,
                    EKritaBlendingModesId.COMPOSITE_VIVID_LIGHT,
                    EKritaBlendingModesId.COMPOSITE_FLAT_LIGHT,
                    EKritaBlendingModesId.COMPOSITE_HARD_LIGHT,
                    EKritaBlendingModesId.COMPOSITE_SOFT_LIGHT_IFS_ILLUSIONS,
                    EKritaBlendingModesId.COMPOSITE_SOFT_LIGHT_PEGTOP_DELPHI,
                    EKritaBlendingModesId.COMPOSITE_SOFT_LIGHT_PHOTOSHOP,
                    EKritaBlendingModesId.COMPOSITE_SOFT_LIGHT_SVG,
                    EKritaBlendingModesId.COMPOSITE_GAMMA_LIGHT,
                    EKritaBlendingModesId.COMPOSITE_GAMMA_ILLUMINATION,
                    EKritaBlendingModesId.COMPOSITE_LIGHTER_COLOR,
                    EKritaBlendingModesId.COMPOSITE_PNORM_A,
                    EKritaBlendingModesId.COMPOSITE_PNORM_B,
                    EKritaBlendingModesId.COMPOSITE_SUPER_LIGHT,
                    EKritaBlendingModesId.COMPOSITE_TINT_IFS_ILLUSIONS,
                    EKritaBlendingModesId.COMPOSITE_FOG_LIGHTEN_IFS_ILLUSIONS,
                    EKritaBlendingModesId.COMPOSITE_EASY_DODGE,
                    EKritaBlendingModesId.COMPOSITE_LUMINOSITY_SAI
                ],
            EKritaBlendingModesId.CATEGORY_MODULO: [
                    EKritaBlendingModesId.COMPOSITE_MOD,
                    EKritaBlendingModesId.COMPOSITE_MOD_CON,
                    EKritaBlendingModesId.COMPOSITE_DIVISIVE_MOD,
                    EKritaBlendingModesId.COMPOSITE_DIVISIVE_MOD_CON,
                    EKritaBlendingModesId.COMPOSITE_MODULO_SHIFT,
                    EKritaBlendingModesId.COMPOSITE_MODULO_SHIFT_CON
                ],
            EKritaBlendingModesId.CATEGORY_NEGATIVE: [
                    EKritaBlendingModesId.COMPOSITE_DIFF,
                    EKritaBlendingModesId.COMPOSITE_EQUIVALENCE,
                    EKritaBlendingModesId.COMPOSITE_ADDITIVE_SUBTRACTIVE,
                    EKritaBlendingModesId.COMPOSITE_EXCLUSION,
                    EKritaBlendingModesId.COMPOSITE_ARC_TANGENT,
                    EKritaBlendingModesId.COMPOSITE_NEGATION
                ],
            EKritaBlendingModesId.CATEGORY_MIX: [
                    EKritaBlendingModesId.COMPOSITE_OVER,
                    EKritaBlendingModesId.COMPOSITE_BEHIND,
                    EKritaBlendingModesId.COMPOSITE_GREATER,
                    EKritaBlendingModesId.COMPOSITE_OVERLAY,
                    EKritaBlendingModesId.COMPOSITE_ERASE,
                    EKritaBlendingModesId.COMPOSITE_ALPHA_DARKEN,
                    EKritaBlendingModesId.COMPOSITE_HARD_MIX,
                    EKritaBlendingModesId.COMPOSITE_HARD_MIX_PHOTOSHOP,
                    EKritaBlendingModesId.COMPOSITE_HARD_MIX_SOFTER_PHOTOSHOP,
                    EKritaBlendingModesId.COMPOSITE_GRAIN_MERGE,
                    EKritaBlendingModesId.COMPOSITE_GRAIN_EXTRACT,
                    EKritaBlendingModesId.COMPOSITE_PARALLEL,
                    EKritaBlendingModesId.COMPOSITE_ALLANON,
                    EKritaBlendingModesId.COMPOSITE_GEOMETRIC_MEAN,
                    EKritaBlendingModesId.COMPOSITE_DESTINATION_ATOP,
                    EKritaBlendingModesId.COMPOSITE_DESTINATION_IN,
                    EKritaBlendingModesId.COMPOSITE_HARD_OVERLAY,
                    EKritaBlendingModesId.COMPOSITE_INTERPOLATION,
                    EKritaBlendingModesId.COMPOSITE_INTERPOLATIONB,
                    EKritaBlendingModesId.COMPOSITE_PENUMBRAA,
                    EKritaBlendingModesId.COMPOSITE_PENUMBRAB,
                    EKritaBlendingModesId.COMPOSITE_PENUMBRAC,
                    EKritaBlendingModesId.COMPOSITE_PENUMBRAD
                ],
            EKritaBlendingModesId.CATEGORY_MISC: [
                    EKritaBlendingModesId.COMPOSITE_BUMPMAP,
                    EKritaBlendingModesId.COMPOSITE_COMBINE_NORMAL,
                    EKritaBlendingModesId.COMPOSITE_DISSOLVE,
                    EKritaBlendingModesId.COMPOSITE_COPY_RED,
                    EKritaBlendingModesId.COMPOSITE_COPY_GREEN,
                    EKritaBlendingModesId.COMPOSITE_COPY_BLUE,
                    EKritaBlendingModesId.COMPOSITE_COPY,
                    EKritaBlendingModesId.COMPOSITE_TANGENT_NORMALMAP
                ],
            EKritaBlendingModesId.CATEGORY_HSY: [
                    EKritaBlendingModesId.COMPOSITE_COLOR,
                    EKritaBlendingModesId.COMPOSITE_HUE,
                    EKritaBlendingModesId.COMPOSITE_SATURATION,
                    EKritaBlendingModesId.COMPOSITE_LUMINIZE,
                    EKritaBlendingModesId.COMPOSITE_DEC_SATURATION,
                    EKritaBlendingModesId.COMPOSITE_INC_SATURATION,
                    EKritaBlendingModesId.COMPOSITE_DEC_LUMINOSITY,
                    EKritaBlendingModesId.COMPOSITE_INC_LUMINOSITY
                ],
            EKritaBlendingModesId.CATEGORY_HSI: [
                    EKritaBlendingModesId.COMPOSITE_COLOR_HSI,
                    EKritaBlendingModesId.COMPOSITE_HUE_HSI,
                    EKritaBlendingModesId.COMPOSITE_SATURATION_HSI,
                    EKritaBlendingModesId.COMPOSITE_INTENSITY,
                    EKritaBlendingModesId.COMPOSITE_DEC_SATURATION_HSI,
                    EKritaBlendingModesId.COMPOSITE_INC_SATURATION_HSI,
                    EKritaBlendingModesId.COMPOSITE_DEC_INTENSITY,
                    EKritaBlendingModesId.COMPOSITE_INC_INTENSITY
                ],
            EKritaBlendingModesId.CATEGORY_HSL: [
                    EKritaBlendingModesId.COMPOSITE_COLOR_HSL,
                    EKritaBlendingModesId.COMPOSITE_HUE_HSL,
                    EKritaBlendingModesId.COMPOSITE_SATURATION_HSL,
                    EKritaBlendingModesId.COMPOSITE_LIGHTNESS,
                    EKritaBlendingModesId.COMPOSITE_DEC_SATURATION_HSL,
                    EKritaBlendingModesId.COMPOSITE_INC_SATURATION_HSL,
                    EKritaBlendingModesId.COMPOSITE_DEC_LIGHTNESS,
                    EKritaBlendingModesId.COMPOSITE_INC_LIGHTNESS
                ],
            EKritaBlendingModesId.CATEGORY_HSV: [
                    EKritaBlendingModesId.COMPOSITE_COLOR_HSV,
                    EKritaBlendingModesId.COMPOSITE_HUE_HSV,
                    EKritaBlendingModesId.COMPOSITE_SATURATION_HSV,
                    EKritaBlendingModesId.COMPOSITE_VALUE,
                    EKritaBlendingModesId.COMPOSITE_DEC_SATURATION_HSV,
                    EKritaBlendingModesId.COMPOSITE_INC_SATURATION_HSV,
                    EKritaBlendingModesId.COMPOSITE_DEC_VALUE,
                    EKritaBlendingModesId.COMPOSITE_INC_VALUE
                ],
            EKritaBlendingModesId.CATEGORY_QUADRATIC: [
                    EKritaBlendingModesId.COMPOSITE_REFLECT,
                    EKritaBlendingModesId.COMPOSITE_GLOW,
                    EKritaBlendingModesId.COMPOSITE_FREEZE,
                    EKritaBlendingModesId.COMPOSITE_HEAT,
                    EKritaBlendingModesId.COMPOSITE_GLEAT,
                    EKritaBlendingModesId.COMPOSITE_HELOW,
                    EKritaBlendingModesId.COMPOSITE_REEZE,
                    EKritaBlendingModesId.COMPOSITE_FRECT,
                    EKritaBlendingModesId.COMPOSITE_FHYRD
                ]
        }

    __BLENDING_MODES = {
            EKritaBlendingModesId.COMPOSITE_ADD:                        i18nc("Blending mode - Addition", "Addition"),
            EKritaBlendingModesId.COMPOSITE_SUBTRACT:                   i18nc("Blending mode - Subtract", "Subtract"),
            EKritaBlendingModesId.COMPOSITE_MULT:                       i18nc("Blending mode - Multiply", "Multiply"),
            EKritaBlendingModesId.COMPOSITE_DIVIDE:                     i18nc("Blending mode - Divide", "Divide"),
            EKritaBlendingModesId.COMPOSITE_INVERSE_SUBTRACT:           i18nc("Blending mode - Inverse Subtract", "Inverse Subtract"),

            EKritaBlendingModesId.COMPOSITE_XOR:                        i18nc("Blending mode - XOR", "XOR"),
            EKritaBlendingModesId.COMPOSITE_OR:                         i18nc("Blending mode - OR", "OR"),
            EKritaBlendingModesId.COMPOSITE_AND:                        i18nc("Blending mode - AND", "AND"),
            EKritaBlendingModesId.COMPOSITE_NAND:                       i18nc("Blending mode - NAND", "NAND"),
            EKritaBlendingModesId.COMPOSITE_NOR:                        i18nc("Blending mode - NOR", "NOR"),
            EKritaBlendingModesId.COMPOSITE_XNOR:                       i18nc("Blending mode - XNOR", "XNOR"),
            EKritaBlendingModesId.COMPOSITE_IMPLICATION:                i18nc("Blending mode - IMPLICATION", "IMPLICATION"),
            EKritaBlendingModesId.COMPOSITE_NOT_IMPLICATION:            i18nc("Blending mode - NOT IMPLICATION", "NOT IMPLICATION"),
            EKritaBlendingModesId.COMPOSITE_CONVERSE:                   i18nc("Blending mode - CONVERSE", "CONVERSE"),
            EKritaBlendingModesId.COMPOSITE_NOT_CONVERSE:               i18nc("Blending mode - NOT CONVERSE", "NOT CONVERSE"),

            EKritaBlendingModesId.COMPOSITE_BURN:                       i18nc("Blending mode - Burn", "Burn"),
            EKritaBlendingModesId.COMPOSITE_LINEAR_BURN:                i18nc("Blending mode - Linear Burn", "Linear Burn"),
            EKritaBlendingModesId.COMPOSITE_DARKEN:                     i18nc("Blending mode - Darken", "Darken"),
            EKritaBlendingModesId.COMPOSITE_GAMMA_DARK:                 i18nc("Blending mode - Gamma Dark", "Gamma Dark"),
            EKritaBlendingModesId.COMPOSITE_DARKER_COLOR:               i18nc("Blending mode - Darker Color", "Darker Color"),
            EKritaBlendingModesId.COMPOSITE_SHADE_IFS_ILLUSIONS:        i18nc("Blending mode - Shade (IFS Illusions)", "Shade (IFS Illusions)"),
            EKritaBlendingModesId.COMPOSITE_FOG_DARKEN_IFS_ILLUSIONS:   i18nc("Blending mode - Fog Darken (IFS Illusions)", "Fog Darken (IFS Illusions)"),
            EKritaBlendingModesId.COMPOSITE_EASY_BURN:                  i18nc("Blending mode - Easy Burn", "Easy Burn"),

            EKritaBlendingModesId.COMPOSITE_DODGE:                      i18nc("Blending mode - Color Dodge", "Color Dodge"),
            EKritaBlendingModesId.COMPOSITE_LINEAR_DODGE:               i18nc("Blending mode - Linear Dodge", "Linear Dodge"),
            EKritaBlendingModesId.COMPOSITE_LIGHTEN:                    i18nc("Blending mode - Lighten", "Lighten"),
            EKritaBlendingModesId.COMPOSITE_LINEAR_LIGHT:               i18nc("Blending mode - Linear Light", "Linear Light"),
            EKritaBlendingModesId.COMPOSITE_SCREEN:                     i18nc("Blending mode - Screen", "Screen"),
            EKritaBlendingModesId.COMPOSITE_PIN_LIGHT:                  i18nc("Blending mode - Pin Light", "Pin Light"),
            EKritaBlendingModesId.COMPOSITE_VIVID_LIGHT:                i18nc("Blending mode - Vivid Light", "Vivid Light"),
            EKritaBlendingModesId.COMPOSITE_FLAT_LIGHT:                 i18nc("Blending mode - Flat Light", "Flat Light"),
            EKritaBlendingModesId.COMPOSITE_HARD_LIGHT:                 i18nc("Blending mode - Hard Light", "Hard Light"),
            EKritaBlendingModesId.COMPOSITE_SOFT_LIGHT_IFS_ILLUSIONS:   i18nc("Blending mode - Soft Light (IFS Illusions)", "Soft Light (IFS Illusions)"),
            EKritaBlendingModesId.COMPOSITE_SOFT_LIGHT_PEGTOP_DELPHI:   i18nc("Blending mode - Soft Light (Pegtop-Delphi)", "Soft Light (Pegtop-Delphi)"),
            EKritaBlendingModesId.COMPOSITE_SOFT_LIGHT_PHOTOSHOP:       i18nc("Blending mode - Soft Light (Photoshop)", "Soft Light (Photoshop)"),
            EKritaBlendingModesId.COMPOSITE_SOFT_LIGHT_SVG:             i18nc("Blending mode - Soft Light (SVG)", "Soft Light (SVG)"),
            EKritaBlendingModesId.COMPOSITE_GAMMA_LIGHT:                i18nc("Blending mode - Gamma Light", "Gamma Light"),
            EKritaBlendingModesId.COMPOSITE_GAMMA_ILLUMINATION:         i18nc("Blending mode - Gamma Illumination", "Gamma Illumination"),
            EKritaBlendingModesId.COMPOSITE_LIGHTER_COLOR:              i18nc("Blending mode - Lighter Color", "Lighter Color"),
            EKritaBlendingModesId.COMPOSITE_PNORM_A:                    i18nc("Blending mode - P-Norm A", "P-Norm A"),
            EKritaBlendingModesId.COMPOSITE_PNORM_B:                    i18nc("Blending mode - P-Norm B", "P-Norm B"),
            EKritaBlendingModesId.COMPOSITE_SUPER_LIGHT:                i18nc("Blending mode - Super Light", "Super Light"),
            EKritaBlendingModesId.COMPOSITE_TINT_IFS_ILLUSIONS:         i18nc("Blending mode - Tint (IFS Illusions)", "Tint (IFS Illusions)"),
            EKritaBlendingModesId.COMPOSITE_FOG_LIGHTEN_IFS_ILLUSIONS:  i18nc("Blending mode - Fog Lighten (IFS Illusions)", "Fog Lighten (IFS Illusions)"),
            EKritaBlendingModesId.COMPOSITE_EASY_DODGE:                 i18nc("Blending mode - Easy Dodge", "Easy Dodge"),
            EKritaBlendingModesId.COMPOSITE_LUMINOSITY_SAI:             i18nc("Blending mode - Luminosity/Shine (SAI)", "Luminosity/Shine (SAI)"),

            EKritaBlendingModesId.COMPOSITE_MOD:                        i18nc("Blending mode - Modulo", "Modulo"),
            EKritaBlendingModesId.COMPOSITE_MOD_CON:                    i18nc("Blending mode - Modulo - Continuous", "Modulo - Continuous"),
            EKritaBlendingModesId.COMPOSITE_DIVISIVE_MOD:               i18nc("Blending mode - Divisive Modulo", "Divisive Modulo"),
            EKritaBlendingModesId.COMPOSITE_DIVISIVE_MOD_CON:           i18nc("Blending mode - Divisive Modulo - Continuous", "Divisive Modulo - Continuous"),
            EKritaBlendingModesId.COMPOSITE_MODULO_SHIFT:               i18nc("Blending mode - Modulo Shift", "Modulo Shift"),
            EKritaBlendingModesId.COMPOSITE_MODULO_SHIFT_CON:           i18nc("Blending mode - Modulo Shift - Continuous", "Modulo Shift - Continuous"),

            EKritaBlendingModesId.COMPOSITE_DIFF:                       i18nc("Blending mode - Difference", "Difference"),
            EKritaBlendingModesId.COMPOSITE_EQUIVALENCE:                i18nc("Blending mode - Equivalence", "Equivalence"),
            EKritaBlendingModesId.COMPOSITE_ADDITIVE_SUBTRACTIVE:       i18nc("Blending mode - Additive Subtractive", "Additive Subtractive"),
            EKritaBlendingModesId.COMPOSITE_EXCLUSION:                  i18nc("Blending mode - Exclusion", "Exclusion"),
            EKritaBlendingModesId.COMPOSITE_ARC_TANGENT:                i18nc("Blending mode - Arcus Tangent", "Arcus Tangent"),
            EKritaBlendingModesId.COMPOSITE_NEGATION:                   i18nc("Blending mode - Negation", "Negation"),

            EKritaBlendingModesId.COMPOSITE_OVER:                       i18nc("Blending mode - Normal", "Normal"),
            EKritaBlendingModesId.COMPOSITE_BEHIND:                     i18nc("Blending mode - Behind", "Behind"),
            EKritaBlendingModesId.COMPOSITE_GREATER:                    i18nc("Blending mode - Greater", "Greater"),
            EKritaBlendingModesId.COMPOSITE_OVERLAY:                    i18nc("Blending mode - Overlay", "Overlay"),
            EKritaBlendingModesId.COMPOSITE_ERASE:                      i18nc("Blending mode - Erase", "Erase"),
            EKritaBlendingModesId.COMPOSITE_ALPHA_DARKEN:               i18nc("Blending mode - Alpha Darken", "Alpha Darken"),
            EKritaBlendingModesId.COMPOSITE_HARD_MIX:                   i18nc("Blending mode - Hard Mix", "Hard Mix"),
            EKritaBlendingModesId.COMPOSITE_HARD_MIX_PHOTOSHOP:         i18nc("Blending mode - Hard Mix (Photoshop)", "Hard Mix (Photoshop)"),
            EKritaBlendingModesId.COMPOSITE_HARD_MIX_SOFTER_PHOTOSHOP:  i18nc("Blending mode - Hard Mix Softer (Photoshop)", "Hard Mix Softer (Photoshop)"),
            EKritaBlendingModesId.COMPOSITE_GRAIN_MERGE:                i18nc("Blending mode - Grain Merge", "Grain Merge"),
            EKritaBlendingModesId.COMPOSITE_GRAIN_EXTRACT:              i18nc("Blending mode - Grain Extract", "Grain Extract"),
            EKritaBlendingModesId.COMPOSITE_PARALLEL:                   i18nc("Blending mode - Parallel", "Parallel"),
            EKritaBlendingModesId.COMPOSITE_ALLANON:                    i18nc("Blending mode - Allanon", "Allanon"),
            EKritaBlendingModesId.COMPOSITE_GEOMETRIC_MEAN:             i18nc("Blending mode - Geometric Mean", "Geometric Mean"),
            EKritaBlendingModesId.COMPOSITE_DESTINATION_ATOP:           i18nc("Blending mode - Destination Atop", "Destination Atop"),
            EKritaBlendingModesId.COMPOSITE_DESTINATION_IN:             i18nc("Blending mode - Destination In", "Destination In"),
            EKritaBlendingModesId.COMPOSITE_HARD_OVERLAY:               i18nc("Blending mode - Hard Overlay", "Hard Overlay"),
            EKritaBlendingModesId.COMPOSITE_INTERPOLATION:              i18nc("Blending mode - Interpolation", "Interpolation"),
            EKritaBlendingModesId.COMPOSITE_INTERPOLATIONB:             i18nc("Blending mode - Interpolation - 2X", "Interpolation - 2X"),
            EKritaBlendingModesId.COMPOSITE_PENUMBRAA:                  i18nc("Blending mode - Penumbra A", "Penumbra A"),
            EKritaBlendingModesId.COMPOSITE_PENUMBRAB:                  i18nc("Blending mode - Penumbra B", "Penumbra B"),
            EKritaBlendingModesId.COMPOSITE_PENUMBRAC:                  i18nc("Blending mode - Penumbra C", "Penumbra C"),
            EKritaBlendingModesId.COMPOSITE_PENUMBRAD:                  i18nc("Blending mode - Penumbra D", "Penumbra D"),

            EKritaBlendingModesId.COMPOSITE_BUMPMAP:                    i18nc("Blending mode - Bumpmap", "Bumpmap"),
            EKritaBlendingModesId.COMPOSITE_COMBINE_NORMAL:             i18nc("Blending mode - Combine Normal Map", "Combine Normal Map"),
            EKritaBlendingModesId.COMPOSITE_DISSOLVE:                   i18nc("Blending mode - Dissolve", "Dissolve"),
            EKritaBlendingModesId.COMPOSITE_COPY_RED:                   i18nc("Blending mode - Copy Red", "Copy Red"),
            EKritaBlendingModesId.COMPOSITE_COPY_GREEN:                 i18nc("Blending mode - Copy Green", "Copy Green"),
            EKritaBlendingModesId.COMPOSITE_COPY_BLUE:                  i18nc("Blending mode - Copy Blue", "Copy Blue"),
            EKritaBlendingModesId.COMPOSITE_COPY:                       i18nc("Blending mode - Copy", "Copy"),
            EKritaBlendingModesId.COMPOSITE_TANGENT_NORMALMAP:          i18nc("Blending mode - Tangent Normalmap", "Tangent Normalmap"),

            EKritaBlendingModesId.COMPOSITE_COLOR:                      i18nc("Blending mode - Color HSY", "Color"),
            EKritaBlendingModesId.COMPOSITE_HUE:                        i18nc("Blending mode - Hue HSY", "Hue"),
            EKritaBlendingModesId.COMPOSITE_SATURATION:                 i18nc("Blending mode - Saturation HSY", "Saturation"),
            EKritaBlendingModesId.COMPOSITE_LUMINIZE:                   i18nc("Blending mode - Luminosity HSY", "Luminosity"),
            EKritaBlendingModesId.COMPOSITE_DEC_SATURATION:             i18nc("Blending mode - Decrease Saturation HSY", "Decrease Saturation"),
            EKritaBlendingModesId.COMPOSITE_INC_SATURATION:             i18nc("Blending mode - Increase Saturation HSY", "Increase Saturation"),
            EKritaBlendingModesId.COMPOSITE_DEC_LUMINOSITY:             i18nc("Blending mode - Decrease Luminosity HSY", "Decrease Luminosity"),
            EKritaBlendingModesId.COMPOSITE_INC_LUMINOSITY:             i18nc("Blending mode - Increase Luminosity HSY", "Increase Luminosity"),

            EKritaBlendingModesId.COMPOSITE_COLOR_HSI:                  i18nc("Blending mode - Color HSI", "Color HSI"),
            EKritaBlendingModesId.COMPOSITE_HUE_HSI:                    i18nc("Blending mode - Hue HSI", "Hue HSI"),
            EKritaBlendingModesId.COMPOSITE_SATURATION_HSI:             i18nc("Blending mode - Saturation HSI", "Saturation HSI"),
            EKritaBlendingModesId.COMPOSITE_INTENSITY:                  i18nc("Blending mode - Intensity HSI", "Intensity"),
            EKritaBlendingModesId.COMPOSITE_DEC_SATURATION_HSI:         i18nc("Blending mode - Decrease Saturation HSI", "Decrease Saturation HSI"),
            EKritaBlendingModesId.COMPOSITE_INC_SATURATION_HSI:         i18nc("Blending mode - Increase Saturation HSI", "Increase Saturation HSI"),
            EKritaBlendingModesId.COMPOSITE_DEC_INTENSITY:              i18nc("Blending mode - Decrease Intensity", "Decrease Intensity"),
            EKritaBlendingModesId.COMPOSITE_INC_INTENSITY:              i18nc("Blending mode - Increase Intensity", "Increase Intensity"),

            EKritaBlendingModesId.COMPOSITE_COLOR_HSL:                  i18nc("Blending mode - Color HSL", "Color HSL"),
            EKritaBlendingModesId.COMPOSITE_HUE_HSL:                    i18nc("Blending mode - Hue HSL", "Hue HSL"),
            EKritaBlendingModesId.COMPOSITE_SATURATION_HSL:             i18nc("Blending mode - Saturation HSL", "Saturation HSL"),
            EKritaBlendingModesId.COMPOSITE_LIGHTNESS:                  i18nc("Blending mode - Lightness HSI", "Lightness"),
            EKritaBlendingModesId.COMPOSITE_DEC_SATURATION_HSL:         i18nc("Blending mode - Decrease Saturation HSL", "Decrease Saturation HSL"),
            EKritaBlendingModesId.COMPOSITE_INC_SATURATION_HSL:         i18nc("Blending mode - Increase Saturation HSL", "Increase Saturation HSL"),
            EKritaBlendingModesId.COMPOSITE_DEC_LIGHTNESS:              i18nc("Blending mode - Decrease Lightness", "Decrease Lightness"),
            EKritaBlendingModesId.COMPOSITE_INC_LIGHTNESS:              i18nc("Blending mode - Increase Lightness", "Increase Lightness"),

            EKritaBlendingModesId.COMPOSITE_COLOR_HSV:                  i18nc("Blending mode - Color HSV", "Color HSV"),
            EKritaBlendingModesId.COMPOSITE_HUE_HSV:                    i18nc("Blending mode - Hue HSV", "Hue HSV"),
            EKritaBlendingModesId.COMPOSITE_SATURATION_HSV:             i18nc("Blending mode - Saturation HSV", "Saturation HSV"),
            EKritaBlendingModesId.COMPOSITE_VALUE:                      i18nc("Blending mode - Value HSV", "Value"),
            EKritaBlendingModesId.COMPOSITE_DEC_SATURATION_HSV:         i18nc("Blending mode - Decrease Saturation HSV", "Decrease Saturation HSV"),
            EKritaBlendingModesId.COMPOSITE_INC_SATURATION_HSV:         i18nc("Blending mode - Increase Saturation HSV", "Increase Saturation HSV"),
            EKritaBlendingModesId.COMPOSITE_DEC_VALUE:                  i18nc("Blending mode - Decrease Value HSV", "Decrease Value"),
            EKritaBlendingModesId.COMPOSITE_INC_VALUE:                  i18nc("Blending mode - Increase Value HSV", "Increase Value"),

            EKritaBlendingModesId.COMPOSITE_REFLECT:                    i18nc("Blending mode - Reflect", "Reflect"),
            EKritaBlendingModesId.COMPOSITE_GLOW:                       i18nc("Blending mode - Glow", "Glow"),
            EKritaBlendingModesId.COMPOSITE_FREEZE:                     i18nc("Blending mode - Freeze", "Freeze"),
            EKritaBlendingModesId.COMPOSITE_HEAT:                       i18nc("Blending mode - Heat", "Heat"),
            EKritaBlendingModesId.COMPOSITE_GLEAT:                      i18nc("Blending mode - Glow-Heat", "Glow-Heat"),
            EKritaBlendingModesId.COMPOSITE_HELOW:                      i18nc("Blending mode - Heat-Glow", "Heat-Glow"),
            EKritaBlendingModesId.COMPOSITE_REEZE:                      i18nc("Blending mode - Reflect-Freeze", "Reflect-Freeze"),
            EKritaBlendingModesId.COMPOSITE_FRECT:                      i18nc("Blending mode - Freeze-Reflect", "Freeze-Reflect"),
            EKritaBlendingModesId.COMPOSITE_FHYRD:                      i18nc("Blending mode - Heat-Glow & Freeze-Reflect Hybrid", "Heat-Glow & Freeze-Reflect Hybrid")
        }

    @staticmethod
    def categoriesIdList():
        """Return list of available categories"""
        return list(EKritaBlendingModes.__CATEGORIES)

    @staticmethod
    def categoryName(id):
        """Return (translated) name for category"""
        if id is None:
            return i18n('None')
        elif id in EKritaBlendingModes.__CATEGORIES:
            return EKritaBlendingModes.__CATEGORIES[id]
        else:
            raise EInvalidValue("Given `id` is not valid")

    @staticmethod
    def categoryBlendingMode(id):
        """Return a list of blending mode Id for given category"""
        if id is None:
            return []
        elif id in EKritaBlendingModes.__CATEGORIES_BLENDING_MODES:
            return list(EKritaBlendingModes.__CATEGORIES_BLENDING_MODES[id])
        else:
            raise EInvalidValue("Given `id` is not valid")

    @staticmethod
    def blendingModeIdList():
        """Return list of available blending mode (without link to category)"""
        return list(EKritaBlendingModes.__BLENDING_MODES)

    @staticmethod
    def blendingModeName(id):
        """Return (translated) name for blending mode"""
        if id is None:
            return []
        elif id in EKritaBlendingModes.__BLENDING_MODES:
            return EKritaBlendingModes.__BLENDING_MODES[id]
        else:
            raise EInvalidValue("Given `id` is not valid")


class EKritaDocument:
    """Provides methods to manage Krita Documents"""

    @staticmethod
    def findLayerById(document, layerId):
        """Find a layer by ID in document
        because Document.nodeByUniqueID() returns a QObject instead of a Node object... :-/
        """
        def find(layerId, parentLayer):
            """sub function called recursively to search layer in document tree"""
            for layer in parentLayer.childNodes():
                if layerId == layer.uniqueId():
                    return layer
                elif len(layer.childNodes()) > 0:
                    returned = find(layerId, layer)
                    if returned is not None:
                        return returned
            return None

        if not isinstance(document, Document):
            raise EInvalidType("Given `document` must be a Krita <Document> type")
        elif not isinstance(layerId, QUuid):
            raise EInvalidType("Given `layerId` must be a valid <QUuid>")

        return find(layerId, document.rootNode())

    @staticmethod
    def findFirstLayerByName(searchFrom, layerName):
        """Find a layer by name in document
        If more than one layer is found in document layers tree, will return the first layer found
        If no layer is found, return None

        The `searchFrom` parameter can be:
        - A Krita Layer (in this case, search in made in sub-nodes)
        - A Krita Document (in this case, search is made from document root node)

        The `layerName` can be a regular expression; just provide layer name with the following form:
        - "re://my_regular_expression

        """
        def find(layerName, isRegex, parentLayer):
            """sub function called recursively to search layer in document tree"""
            for layer in reversed(parentLayer.childNodes()):
                if isRegex is False and layerName == layer.name():
                    return layer
                elif isRegex is True and (reResult := re.match(layerName, layer.name())):
                    return layer
                elif len(layer.childNodes()) > 0:
                    returned = find(layerName, isRegex, layer)
                    if returned is not None:
                        return returned
            return None

        if not (isinstance(searchFrom, Document) or isinstance(searchFrom, Layer)):
            raise EInvalidType("Given `searchFrom` must be a Krita <Layer> or a Krita <Document> type")
        elif not isinstance(layerName, str):
            raise EInvalidType("Given `layerName` must be a valid <str>")

        parentLayer = searchFrom
        if isinstance(searchFrom, Document):
            # a document has been provided, use document root layer
            parentLayer = searchFrom.rootNode()

        if (reResult := re.match("^re://(.*)", layerName)):
            # retrieve given regular expression
            layerName = reResult.group(1)
            return find(layerName, True, parentLayer)
        else:
            return find(layerName, False, parentLayer)

        return None

    @staticmethod
    def findLayersByName(searchFrom, layerName):
        """Find layer(s) by name
        Return a list of all layers for which name is matching given layer name
        If no layer is found, return empty list

        The `searchFrom` parameter can be:
        - A Krita Layer (in this case, search in made in sub-nodes)
        - A Krita Document (in this case, search is made from document root node)

        The `layerName` can be a regular expression; just provide layer name with the following form:
        - "re://my_regular_expression
        """
        def find(layerName, isRegex, parentLayer):
            """sub function called recursively to search layer in document tree"""
            returned = []
            for layer in reversed(parentLayer.childNodes()):
                if isRegex is False and layerName == layer.name():
                    returned.append(layer)
                elif isRegex is True and (reResult := re.match(layerName, layer.name())):
                    returned.append(layer)
                elif len(layer.childNodes()) > 0:
                    found = find(layerName, isRegex, layer)
                    if found is not None:
                        returned += found
            return returned

        if not (isinstance(searchFrom, Document) or isinstance(searchFrom, Layer)):
            raise EInvalidType("Given `searchFrom` must be a Krita <Layer> or a Krita <Document> type")
        elif not isinstance(layerName, str):
            raise EInvalidType("Given `layerName` must be a valid <str> (current: {0})".format(type(layerName)))

        parentLayer = searchFrom
        if isinstance(searchFrom, Document):
            # a document has been provided, use document root layer
            parentLayer = searchFrom.rootNode()

        if (reResult := re.match("^re://(.*)", layerName)):
            # retrieve given regular expression
            layerName = reResult.group(1)
            return find(layerName, True, parentLayer)
        else:
            return find(layerName, False, parentLayer)

        return []

    @staticmethod
    def getLayers(searchFrom, recursiveSubLayers=False):
        """Return a list of all layers

        The `searchFrom` parameter can be:
        - A Krita Layer (in this case, return all sub-nodes from given layer)
        - A Krita Document (in this case, return all sub-nodes from document root node)

        If `recursiveSubLayers` is True, also return all subLayers
        """
        def find(recursiveSubLayers, parentLayer):
            """sub function called recursively to search layer in document tree"""
            returned = []
            for layer in reversed(parentLayer.childNodes()):
                returned.append(layer)
                if recursiveSubLayers and len(layer.childNodes()) > 0:
                    found = find(recursiveSubLayers, layer)
                    if found is not None:
                        returned += found
            return returned

        if not (isinstance(searchFrom, Document) or isinstance(searchFrom, Layer)):
            raise EInvalidType("Given `searchFrom` must be a Krita <Layer> or a Krita <Document> type")
        elif not isinstance(recursiveSubLayers, bool):
            raise EInvalidType("Given `recursiveSubLayers` must be a <bool>")

        parentLayer = searchFrom
        if isinstance(searchFrom, Document):
            # a document has been provided, use document root layer
            parentLayer = searchFrom.rootNode()

        return find(recursiveSubLayers, parentLayer)

    @staticmethod
    def getLayerFromPath(searchFrom, path):
        """Return a layer from given path
        If no layer is found, return None

        The `searchFrom` parameter can be:
        - A Krita Document (in this case, return all sub-nodes from document root node)
        """
        def find(pathNodes, level, parentLayer):
            """sub function called recursively to search layer in document tree"""
            for layer in reversed(parentLayer.childNodes()):
                if layer.name() == pathNodes[level]:
                    if level == len(pathNodes) - 1:
                        return layer
                    elif len(layer.childNodes()) > 0:
                        return find(pathNodes, level + 1, layer)
            return None

        if not isinstance(searchFrom, Document):
            raise EInvalidType("Given `searchFrom` must be a Krita <Document> type")
        elif not isinstance(path, str):
            raise EInvalidType("Given `path` must be a <str>")

        pathNodes = re.findall(r'(?:[^/"]|"(?:\\.|[^"])*")+', path)

        if pathNodes is not None:
            pathNodes = [re.sub(r'^"|"$', '', pathNode) for pathNode in pathNodes]

        return find(pathNodes, 0, searchFrom.rootNode())


class EKritaNode:
    """Provides methods to manage Krita Nodes"""

    class ProjectionMode(Enum):
        """Projection modes for toQImage(), toQPixmap()"""
        FALSE = 0
        TRUE = 1
        AUTO = 2

    __projectionMode = ProjectionMode.AUTO

    @staticmethod
    def __sleep(value):
        """Sleep for given number of milliseconds"""
        loop = QEventLoop()
        QTimer.singleShot(value, loop.quit)
        loop.exec()

    @staticmethod
    def path(layerNode):
        """Return `layerNode` path in tree

        Example
        =======
            rootnode
             +-- groupLayer1
                 +-- groupLayer2
                     +-- theNode
                     +-- theNode with / character

            return '/groupLayer1/groupLayer2/theNode'
            return '/groupLayer1/groupLayer2/"theNode with / character"'
        """
        def parentPath(layerNode):
            if layerNode.parentNode() is None or layerNode.parentNode().parentNode() is None:
                return ''
            else:
                if '/' in layerNode.name():
                    return f'{parentPath(layerNode.parentNode())}/"{layerNode.name()}"'
                else:
                    return f'{parentPath(layerNode.parentNode())}/{layerNode.name()}'

        if not isinstance(layerNode, Node):
            raise EInvalidType("Given `layerNode` must be a valid Krita <Node> ")

        return parentPath(layerNode)

    @staticmethod
    def toQImage(layerNode, rect=None, projectionMode=None):
        """Return `layerNode` content as a QImage (as ARGB32)

        The `rect` value can be:
        - None, in this case will return all `layerNode` content
        - A QRect() object, in this case return `layerNode` content reduced to given rectangle bounds
        - A Krita document, in this case return `layerNode` content reduced to document bounds
        """
        if layerNode is None:
            raise EInvalidValue("Given `layerNode` can't be None")

        if type(layerNode) == QObject:
            # NOTE: layerNode can be a QObject...
            #       that's weird, but document.nodeByUniqueID() return a QObject for a paintlayer (other Nodes seems to be Ok...)
            #       it can sound strange but in this case the returned QObject is a QObject iwht Node properties
            #       so, need to check if QObject have expected methods
            if (hasattr(layerNode, 'type') and
               hasattr(layerNode, 'bounds') and
               hasattr(layerNode, 'childNodes') and
               hasattr(layerNode, 'colorModel') and
               hasattr(layerNode, 'colorDepth') and
               hasattr(layerNode, 'colorProfile') and
               hasattr(layerNode, 'setColorSpace') and
               hasattr(layerNode, 'setPixelData')):
                pass
            else:
                # consider that it's not a node
                raise EInvalidType("Given `layerNode` must be a valid Krita <Node> ")
        elif not isinstance(layerNode, Node):
            raise EInvalidType("Given `layerNode` must be a valid Krita <Node> ")

        if rect is None:
            rect = layerNode.bounds()
        elif isinstance(rect, Document):
            rect = rect.bounds()
        elif not isinstance(rect, QRect):
            raise EInvalidType("Given `rect` must be a valid Krita <Document>, a <QRect> or None")

        if projectionMode is None:
            projectionMode = EKritaNode.__projectionMode
        if projectionMode == EKritaNode.ProjectionMode.AUTO:
            childNodes = layerNode.childNodes()
            # childNodes can return be None!?
            if childNodes and len(childNodes) == 0:
                projectionMode = EKritaNode.ProjectionMode.FALSE
            else:
                projectionMode = EKritaNode.ProjectionMode.TRUE

        # Need to check what todo for:
        # - masks (8bit/pixels)
        # - other color space (need to convert to 8bits/rgba...?)
        if (layerNode.type() in ('transparencymask', 'filtermask', 'transformmask', 'selectionmask') or
           layerNode.colorModel() != 'RGBA' or
           layerNode.colorDepth() != 'U8'):
            # pixelData/projectionPixelData return a 8bits/pixel matrix
            # didn't find how to convert pixel data to QImlage then use thumbnail() function
            return layerNode.thumbnail(rect.width(), rect.height())
        else:
            if projectionMode == EKritaNode.ProjectionMode.TRUE:
                return QImage(layerNode.projectionPixelData(rect.left(), rect.top(), rect.width(), rect.height()), rect.width(), rect.height(), QImage.Format_ARGB32)
            else:
                return QImage(layerNode.pixelData(rect.left(), rect.top(), rect.width(), rect.height()), rect.width(), rect.height(), QImage.Format_ARGB32)

    @staticmethod
    def toQPixmap(layerNode, rect=None, projectionMode=None):
        """Return `layerNode` content as a QPixmap (as ARGB32)

        If the `projection` value is True, returned :


        The `rect` value can be:
        - None, in this case will return all `layerNode` content
        - A QRect() object, in this case return `layerNode` content reduced to given rectangle bounds
        - A Krita document, in this case return `layerNode` content reduced to document bounds
        """
        return QPixmap.fromImage(EKritaNode.toQImage(layerNode, rect, projectionMode))

    @staticmethod
    def fromQImage(layerNode, image, position=None):
        """Paste given `image` to `position` in '`layerNode`

        The `position` value can be:
        - None, in this case, pixmap will be pasted at position (0, 0)
        - A QPoint() object, pixmap will be pasted at defined position
        """
        # NOTE: layerNode can be a QObject...
        #       that's weird, but document.nodeByUniqueID() return a QObject for a paintlayer (other Nodes seems to be Ok...)
        #       it can sound strange but in this case the returned QObject is a QObject iwht Node properties
        #       so, need to check if QObject have expected methods
        if type(layerNode) == QObject():
            if (hasattr(layerNode, 'type') and
               hasattr(layerNode, 'colorModel') and
               hasattr(layerNode, 'colorDepth') and
               hasattr(layerNode, 'colorProfile') and
               hasattr(layerNode, 'setColorSpace') and
               hasattr(layerNode, 'setPixelData')):
                pass
            else:
                # consider that it's not a node
                raise EInvalidType("Given `layerNode` must be a valid Krita <Node> ")
        elif not isinstance(layerNode, Node):
            raise EInvalidType("Given `layerNode` must be a valid Krita <Node> ")

        if not isinstance(image, QImage):
            raise EInvalidType("Given `image` must be a valid <QImage> ")

        if position is None:
            position = QPoint(0, 0)

        if not isinstance(position, QPoint):
            raise EInvalidType("Given `position` must be a valid <QPoint> ")

        layerNeedBackConversion = False
        layerColorModel = layerNode.colorModel()
        layerColorDepth = layerNode.colorDepth()
        layerColorProfile = layerNode.colorProfile()

        if layerColorModel != "RGBA" or layerColorDepth != 'U8':
            # we need to convert layer to RGBA/U8
            layerNode.setColorSpace("RGBA", "U8", "sRGB-elle-V2-srgbtrc.icc")
            layerNeedBackConversion = True

        ptr = image.bits()
        ptr.setsize(image.byteCount())

        layerNode.setPixelData(QByteArray(ptr.asstring()), position.x(), position.y(), image.width(), image.height())

        if layerNeedBackConversion:
            layerNode.setColorSpace(layerColorModel, layerColorDepth, layerColorProfile)

    @staticmethod
    def fromQPixmap(layerNode, pixmap, position=None):
        """Paste given `pixmap` to `position` in '`layerNode`

        The `position` value can be:
        - None, in this case, pixmap will be pasted at position (0, 0)
        - A QPoint() object, pixmap will be pasted at defined position
        """
        if not isinstance(pixmap, QPixmap):
            raise EInvalidType("Given `pixmap` must be a valid <QPixmap> ")

        if position is None:
            position = QPoint(0, 0)

        EKritaNode.fromQImage(layerNode, pixmap.toImage(), position)

    @staticmethod
    def fromSVG(layerNode, svgContent, document=None):
        """Paste given `svgContent` to `position` in '`layerNode`

        Given `layerNode` must be a 'vectorlayer'

        The `position` value can be:
        - None, in this case, pixmap will be pasted at position (0, 0)
        - A QPoint() object, pixmap will be pasted at defined position

        Note:
        - If document is None, consider that active document contains layer
        - If document is provided, it must contains layerNode

        Method return a list of shapes (shape inserted into layer)
        """
        if isinstance(svgContent, str):
            svgContent = svgContent.encode()

        if not isinstance(svgContent, bytes):
            raise EInvalidType("Given `svgContent` must be a valid <str> or <bytes> SVG document")

        if not isinstance(layerNode, Node) or layerNode.type() != 'vectorlayer':
            raise EInvalidType("Given `layerNode` must be a valid <VectorLayer>")

        if document is None:
            document = Krita.instance().activeDocument()

        if not isinstance(document, Document):
            raise EInvalidType("Given `layerNode` must be a valid <Document > ")

        shapes = [shape for shape in layerNode.shapes()]

        activeNode = document.activeNode()
        document.setActiveNode(layerNode)
        document.waitForDone()

        # Note: following sleep() is here because waitForDone() doesn't seems to
        #       wait for active node changed...
        #       set an arbitrary sleep() delay allows to ensure that node is active
        #       at the end of method execution
        #       hope current delay is not too short (works for me... but can't put
        #       a too long delay)
        #
        #       Problem occurs with krita 4.4.2 & and tested Krita plus/next tested [2020-01-05]
        EKritaNode.__sleep(100)

        mimeContent = QMimeData()
        mimeContent.setData('image/svg', svgContent)
        mimeContent.setData('BCIGNORE', b'')
        QGuiApplication.clipboard().setMimeData(mimeContent)
        Krita.instance().action('edit_paste').trigger()

        newShapes = [shape for shape in layerNode.shapes() if shape not in shapes]

        return newShapes

    @staticmethod
    def above(layerNode):
        """Return node above given `layerNode`

        If there's no node above given layer, return None"""

        if layerNode is None:
            return None

        if not isinstance(layerNode, Node):
            raise EInvalidType("Given `layerNode` must be a valid Krita <Node> ")

        returnNext = False
        for layer in layerNode.parentNode().childNodes():
            if returnNext:
                return layer
            elif layer == layerNode:
                returnNext = True

        return None

    @staticmethod
    def below(layerNode):
        """Return node below given `layerNode`

        If there's no node below given layer, return None"""

        if layerNode is None:
            return None

        if not isinstance(layerNode, Node):
            raise EInvalidType("Given `layerNode` must be a valid Krita <Node> ")

        prevNode = None
        for layer in layerNode.parentNode().childNodes():
            if layer == layerNode:
                return prevNode
            prevNode = layer

        return None
