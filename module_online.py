from gdo.base.Application import Application
from gdo.base.Cache import Cache
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.core.GDO_User import GDO_User
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

    def gdo_init(self):
        Application.EVENTS.subscribe('user_setting_last_activity_changed', self.on_last_activity_changed)
        Application.EVENTS.subscribe('user_logout', self.on_user_logout)

    def on_last_activity_changed(self, user: GDO_User, val):
        self.on_clear_cache()

    def on_user_logout(self, user: GDO_User):
        Cache.remove('online_users')

    def on_clear_cache(self):
        Cache.remove('online_users')

    def gdo_init_sidebar(self, page: 'GDT_Page'):
        cached = Cache.get('online_users', 'all')
        panel = cached or GDT_OnlinePanel()
        if not cached:
            Cache.set('online_users', 'all', panel)
        self.cfg_page_location().add_field(panel)
