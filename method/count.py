from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_Dict import GDT_Dict


class count(Method):
    def gdo_execute(self) -> GDT:
        online = self.gdo_module()
        return GDT_Dict(online.online_counts())
