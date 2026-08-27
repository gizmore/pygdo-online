from gdo.base.Application import Application
from gdo.base.Cache import Cache
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.Util import module_enabled
from gdo.base.util.href import href
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_Container import GDT_Container
from gdo.online.GDT_OnlinePanel import GDT_OnlinePanel
from gdo.ui.GDT_Page import GDT_Page
from gdo.ui.GDT_PageLocation import GDT_PageLocation
from gdo.ui.GDT_Link import GDT_Link
from gdo.user.module_user import module_user


class module_online(GDO_Module):

    def __init__(self):
        super().__init__()
        self._priority = 40

    def gdo_friendencies(self) -> list:
        return [
            'maps',
        ]

    def gdo_module_config(self) -> list[GDT]:
        return [
            GDT_PageLocation('online_bar_location').not_null().initial('_bottom_bar'),
        ]

    def cfg_page_location(self) -> GDT_Container:
        return self.get_config_value('online_bar_location')

    def gdo_init(self):
        Application.EVENTS.subscribe('user_setting_last_activity_changed', self.on_last_activity_changed)
        Application.EVENTS.subscribe('user_logout', self.on_user_logout)

    def gdo_load_scripts(self, page: 'GDT_Page'):
        if module_enabled('maps'):
            self.add_js('js/pygdo-online-map.js')
            self.add_css('css/pygdo-online.css')

    def on_last_activity_changed(self, user: GDO_User, val):
        self.on_clear_cache()

    async def on_user_logout(self, user: GDO_User):
        Cache.remove('online_users')

    def on_clear_cache(self):
        Cache.remove('online_users')

    def online_users(self) -> list[GDO_User]:
        """Return active primary accounts, not their linked connector identities."""
        cut = module_user.instance().get_activity_cut_date()
        return [
            user for user in GDO_User.table().with_settings_result([('last_activity', '>=', cut)])
            if user.gdo_val('user_link') is None
        ]

    def online_users_with_positions(self) -> list[dict]:
        """Return the current online users that have a stored map position."""
        from gdo.maps.GDO_UserPos import GDO_UserPos

        positions = {}
        for position in GDO_UserPos.table().select().order('up_created DESC').exec():
            positions.setdefault(position.gdo_val('up_user'), position)
        users = []
        for user in self.online_users():
            if position := positions.get(user.get_id()):
                users.append({
                    'name': user.get_name_sid(),
                    'profile_url': href('user', 'profile', f'&for={user.get_name_sid()}'),
                    'avatar': self.avatar_href(user),
                    'lat': float(position.gdo_val('up_pos_lat')),
                    'lng': float(position.gdo_val('up_pos_lng')),
                })
        return users

    @staticmethod
    def avatar_href(user: GDO_User) -> str | None:
        if not module_enabled('avatar'):
            return None
        from gdo.avatar.GDT_Avatar import GDT_Avatar
        return GDT_Avatar('avatar').for_user(user).href_render()

    def gdo_init_sidebar(self, page: 'GDT_Page'):
        """
        Put the who is online into a page bar.
        """
        self.cfg_page_location().add_field(GDT_OnlinePanel())
        if module_enabled('maps'):
            count = len(self.online_users())
            page._left_bar.add_field(GDT_Link().href(self.href('map')).text('mt_online_map', (count,)))
