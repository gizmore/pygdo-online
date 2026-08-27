from gdo.base.Util import jsn
from gdo.base.Util import module_enabled
from gdo.ui.MethodPage import MethodPage


class map(MethodPage):

    def gdo_connectors(self) -> str:
        return 'web'

    def gdo_has_permission(self, user) -> bool:
        return module_enabled('maps')

    def gdo_page_vars(self) -> dict:
        users = self.gdo_module().online_users_with_positions()
        return {
            'users_json': jsn(users).decode(),
        }
