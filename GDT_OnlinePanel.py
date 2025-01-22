from gdo.base.Trans import t
from gdo.core.GDO_User import GDO_User
from gdo.message.GDT_HTML import GDT_HTML
from gdo.ui.GDT_Panel import GDT_Panel
from gdo.user.GDT_ProfileLink import GDT_ProfileLink
from gdo.user.module_user import module_user


class GDT_OnlinePanel(GDT_Panel):

    def __init__(self):
        super().__init__()
        cut = module_user.instance().get_activity_cut_date()
        for user in GDO_User.table().with_setting_result([('last_activity', '>=', cut)]):
            self.add_field(GDT_ProfileLink().user(user))
        self.get_fields().insert(0, GDT_HTML().text(t('online_users', (str(len(self._fields)),))))
