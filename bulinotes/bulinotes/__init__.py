from krita import DockWidgetFactory, DockWidgetFactoryBase
from .bulinotes import *


instance = Krita.instance()
bnDocker = DockWidgetFactory(f'{EXTENSION_ID}_current',
                                    DockWidgetFactoryBase.DockRight,
                                    BuliNotesDocker)
instance.addDockWidgetFactory(bnDocker)
