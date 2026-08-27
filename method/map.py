from gdo.base.Util import jsn
from gdo.base.Util import module_enabled
from gdo.base.Trans import t
from gdo.online.module_online import module_online
from gdo.ui.MethodPage import MethodPage


class map(MethodPage):

    def gdo_connectors(self) -> str:
        return 'web'

    def gdo_has_permission(self, user) -> bool:
        return module_enabled('maps')

    def gdo_render_title(self) -> str:
        return t('mt_online_map', (len(module_online.instance().online_users()),))

    def gdo_page_vars(self) -> dict:
        users = module_online.instance().online_users_with_positions()
        return {
            'users_json': jsn(users).decode(),
        }
