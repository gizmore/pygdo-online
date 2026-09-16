from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_List import GDT_List
from gdo.user.GDT_ProfileLink import GDT_ProfileLink


class users(Method):
    """The current online roster for the website overlay."""

    def gdo_execute(self) -> GDT:
        rows = GDT_List()
        for user in self.gdo_module().online_users():
            profile = GDT_ProfileLink().user(user)
            avatar = user.gdt_user_settings().KNOWN.get('avatar_file')
            rows.append({
                'name': user.render_name(),
                'profile': profile.render_href(),
                'avatar': avatar.for_user(user).href_render() if avatar else None,
            })
        return rows
