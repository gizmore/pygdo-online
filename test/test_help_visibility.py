import unittest
from types import SimpleNamespace
from unittest.mock import patch

from gdo.online.method.count import count
from gdo.online.method.online import online
from gdo.online.method.users import users


class OnlineHelpVisibilityTest(unittest.TestCase):
    def test_rosters_hidden_count_visible(self):
        for method in (online, users):
            self.assertTrue(method.gdo_method_hidden(object.__new__(method)))
        with patch.object(count, 'gdo_module', return_value=SimpleNamespace()):
            self.assertFalse(count.gdo_method_hidden(object.__new__(count)))
