from gdo.base.Trans import t
from gdo.core.GDT_Container import GDT_Container
from gdo.message.GDT_HTML import GDT_HTML
from gdo.user.GDT_ProfileLink import GDT_ProfileLink


class GDT_OnlinePanel(GDT_Container):

    def __init__(self):
        super().__init__()
        from gdo.online.module_online import module_online
        for user in module_online.instance().online_users():
            self.add_field(GDT_ProfileLink().user(user))
        self._fields.insert(0, GDT_HTML().text(t('online_users', (str(len(self._fields)),))))
