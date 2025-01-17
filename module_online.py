from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.core.GDT_Container import GDT_Container
from gdo.online.GDT_OnlinePanel import GDT_OnlinePanel
from gdo.ui.GDT_Page import GDT_Page
from gdo.ui.GDT_PageLocation import GDT_PageLocation


class module_online(GDO_Module):

    def __init__(self):
        super().__init__()
        self._priority = 40

    def gdo_module_config(self) -> list[GDT]:
        return [
            GDT_PageLocation('online_bar_location').not_null().initial('_bottom_bar'),
        ]

    def cfg_page_location(self) -> GDT_Container:
        return self.get_config_value('online_bar_location')

    def gdo_init_sidebar(self, page: 'GDT_Page'):
        location = self.cfg_page_location()
        location.add_field(GDT_OnlinePanel())
