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


from pktk.modules.settings import (
                        Settings,
                        SettingsFmt,
                        SettingsKey,
                        SettingsRule
                    )
from pktk.widgets.wcolorselector import WColorPicker

class BNSettingsKey(SettingsKey):
    """Configuration keys"""
    CONFIG_EDITOR_TEXT_COLORPICKER_COMPACT=                                     'config.editor.text.colorPicker.compact'
    CONFIG_EDITOR_TEXT_COLORPICKER_PALETTE_VISIBLE=                             'config.editor.text.colorPicker.palette.visible'
    CONFIG_EDITOR_TEXT_COLORPICKER_PALETTE_DEFAULT=                             'config.editor.text.colorPicker.palette.default'
    CONFIG_EDITOR_TEXT_COLORPICKER_CWHEEL_VISIBLE=                              'config.editor.text.colorPicker.colorWheel.visible'
    CONFIG_EDITOR_TEXT_COLORPICKER_CWHEEL_CPREVIEW=                             'config.editor.text.colorPicker.colorWheel.colorPreview'
    CONFIG_EDITOR_TEXT_COLORPICKER_CCOMBINATION=                                'config.editor.text.colorPicker.colorCombination'
    CONFIG_EDITOR_TEXT_COLORPICKER_CCSS=                                        'config.editor.text.colorPicker.colorCss.visible'
    CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_RGB_VISIBLE=                         'config.editor.text.colorPicker.colorSlider.rgb.visible'
    CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_RGB_ASPCT=                           'config.editor.text.colorPicker.colorSlider.rgb.asPct'
    CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_CMYK_VISIBLE=                        'config.editor.text.colorPicker.colorSlider.cmyk.visible'
    CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_CMYK_ASPCT=                          'config.editor.text.colorPicker.colorSlider.cmyk.asPct'
    CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSL_VISIBLE=                         'config.editor.text.colorPicker.colorSlider.hsl.visible'
    CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSL_ASPCT=                           'config.editor.text.colorPicker.colorSlider.hsl.asPct'
    CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSV_VISIBLE=                         'config.editor.text.colorPicker.colorSlider.hsv.visible'
    CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSV_ASPCT=                           'config.editor.text.colorPicker.colorSlider.hsv.asPct'

    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_COMPACT=                               'config.editor.scratchpad.colorPicker.compact'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_PALETTE_VISIBLE=                       'config.editor.scratchpad.colorPicker.palette.visible'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_PALETTE_DEFAULT=                       'config.editor.scratchpad.colorPicker.palette.default'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CWHEEL_VISIBLE=                        'config.editor.scratchpad.colorPicker.colorWheel.visible'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CWHEEL_CPREVIEW=                       'config.editor.scratchpad.colorPicker.colorWheel.colorPreview'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CCOMBINATION=                          'config.editor.scratchpad.colorPicker.colorCombination'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CCSS=                                  'config.editor.scratchpad.colorPicker.colorCss.visible'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_RGB_VISIBLE=                   'config.editor.scratchpad.colorPicker.colorSlider.rgb.visible'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_RGB_ASPCT=                     'config.editor.scratchpad.colorPicker.colorSlider.rgb.asPct'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_CMYK_VISIBLE=                  'config.editor.scratchpad.colorPicker.colorSlider.cmyk.visible'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_CMYK_ASPCT=                    'config.editor.scratchpad.colorPicker.colorSlider.cmyk.asPct'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_HSL_VISIBLE=                   'config.editor.scratchpad.colorPicker.colorSlider.hsl.visible'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_HSL_ASPCT=                     'config.editor.scratchpad.colorPicker.colorSlider.hsl.asPct'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_HSV_VISIBLE=                   'config.editor.scratchpad.colorPicker.colorSlider.hsv.visible'
    CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_HSV_ASPCT=                     'config.editor.scratchpad.colorPicker.colorSlider.hsv.asPct'

    CONFIG_EDITOR_TYPE_BRUSHES_ZOOMLEVEL=                                       'config.editor.type.brushes.list.zoomLevel'
    CONFIG_EDITOR_TYPE_LINKEDLAYERS_LIST_ZOOMLEVEL=                             'config.editor.type.linkedLayers.list.zoomLevel'
    CONFIG_EDITOR_TYPE_LINKEDLAYERS_ADDLAYERTREE_ZOOMLEVEL=                     'config.editor.type.linkedLayers.addLayerTree.zoomLevel'

class BNSettings(Settings):
    """BuliNote settings manager"""

    def __init__(self):
        super(BNSettings, self).__init__('bulinotes')

        self.setRules([
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_COMPACT,                      True,       SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_PALETTE_VISIBLE,              True,       SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_PALETTE_DEFAULT,              "Default",  SettingsFmt(str)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CWHEEL_VISIBLE,               False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CWHEEL_CPREVIEW,              True,       SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CCOMBINATION,                 0,          SettingsFmt(int, [0,1,2,3,4,5])),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CCSS,                         False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_RGB_VISIBLE,          False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_RGB_ASPCT,            False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_CMYK_VISIBLE,         False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_CMYK_ASPCT,           False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSL_VISIBLE,          False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSL_ASPCT,            False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSV_VISIBLE,          False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSV_ASPCT,            False,      SettingsFmt(bool)),

            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_COMPACT,                False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_PALETTE_VISIBLE,        False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_PALETTE_DEFAULT,        "Default",  SettingsFmt(str)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CWHEEL_VISIBLE,         True,       SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CWHEEL_CPREVIEW,        True,       SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CCOMBINATION,           0,          SettingsFmt(int, [0,1,2,3,4,5])),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CCSS,                   False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_RGB_VISIBLE,    False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_RGB_ASPCT,      False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_CMYK_VISIBLE,   False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_CMYK_ASPCT,     False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_HSL_VISIBLE,    True,       SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_HSL_ASPCT,      False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_HSV_VISIBLE,    False,      SettingsFmt(bool)),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_SCRATCHPAD_COLORPICKER_CSLIDER_HSV_ASPCT,      False,      SettingsFmt(bool)),

            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TYPE_BRUSHES_ZOOMLEVEL,                        3,          SettingsFmt(int, [0,1,2,3,4])),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TYPE_LINKEDLAYERS_LIST_ZOOMLEVEL,              4,          SettingsFmt(int, [0,1,2,3,4,5])),
            SettingsRule(BNSettingsKey.CONFIG_EDITOR_TYPE_LINKEDLAYERS_ADDLAYERTREE_ZOOMLEVEL,      2,          SettingsFmt(int, [0,1,2,3,4,5]))
        ])

    @staticmethod
    def getTxtColorPickerLayout():
        """Convert text color picker layout from settings to layout"""
        # build a dummy color picker
        tmpColorPicker=WColorPicker()
        tmpColorPicker.setOptionCompactUi(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_COMPACT))
        tmpColorPicker.setOptionShowColorPalette(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_PALETTE_VISIBLE))
        tmpColorPicker.setOptionColorPalette(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_PALETTE_DEFAULT))
        tmpColorPicker.setOptionShowColorWheel(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CWHEEL_VISIBLE))
        tmpColorPicker.setOptionShowPreviewColor(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CWHEEL_CPREVIEW))
        tmpColorPicker.setOptionShowColorCombination(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CCOMBINATION))
        tmpColorPicker.setOptionShowCssRgb(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CCSS))
        tmpColorPicker.setOptionShowColorRGB(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_RGB_VISIBLE))
        tmpColorPicker.setOptionDisplayAsPctColorRGB(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_RGB_ASPCT))
        tmpColorPicker.setOptionShowColorCMYK(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_CMYK_VISIBLE))
        tmpColorPicker.setOptionDisplayAsPctColorCMYK(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_CMYK_ASPCT))
        tmpColorPicker.setOptionShowColorHSV(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSL_VISIBLE))
        tmpColorPicker.setOptionDisplayAsPctColorHSV(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSL_ASPCT))
        tmpColorPicker.setOptionShowColorHSL(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSV_VISIBLE))
        tmpColorPicker.setOptionDisplayAsPctColorHSL(BNSettings.get(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSV_ASPCT))
        tmpColorPicker.setOptionShowColorAlpha(False)
        return tmpColorPicker.optionLayout()

    @staticmethod
    def setTxtColorPickerLayout(layout):
        """Convert text color picker layout from settings to layout"""
        # build a dummy color picker
        tmpColorPicker=WColorPicker()
        tmpColorPicker.setOptionLayout(layout)

        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_COMPACT, tmpColorPicker.optionCompactUi())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_PALETTE_VISIBLE, tmpColorPicker.optionShowColorPalette())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_PALETTE_DEFAULT, tmpColorPicker.optionColorPalette())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CWHEEL_VISIBLE, tmpColorPicker.optionShowColorWheel())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CWHEEL_CPREVIEW, tmpColorPicker.optionShowPreviewColor())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CCOMBINATION, tmpColorPicker.optionShowColorCombination())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CCSS, tmpColorPicker.optionShowColorCssRGB())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_RGB_VISIBLE, tmpColorPicker.optionShowColorRGB())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_RGB_ASPCT, tmpColorPicker.optionDisplayAsPctColorRGB())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_CMYK_VISIBLE, tmpColorPicker.optionShowColorCMYK())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_CMYK_ASPCT, tmpColorPicker.optionDisplayAsPctColorCMYK())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSL_VISIBLE, tmpColorPicker.optionShowColorHSL())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSL_ASPCT, tmpColorPicker.optionDisplayAsPctColorHSL())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSV_VISIBLE, tmpColorPicker.optionShowColorHSV())
        BNSettings.set(BNSettingsKey.CONFIG_EDITOR_TEXT_COLORPICKER_CSLIDER_HSV_ASPCT, tmpColorPicker.optionDisplayAsPctColorHSV())
