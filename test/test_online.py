import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdotest.TestUtil import web_plug, WebPlug, GDOTestCase, install_module


class OnlineUsersTest(GDOTestCase):

    def setUp(self):
        super().setUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        install_module('online')
        loader.init_modules(True, True)
        WebPlug.COOKIES = {}

    def test_01_online_users(self):
        web_plug('core.welcome.html').user('gizmore').exec()
        web_plug('core.welcome.html').user('gizmore').exec()
        out = web_plug('core.welcome.html').user('gizmore').exec()
        self.assertIn('Users Online<a class="gdt-link"', out, 'Online users broken')


if __name__ == '__main__':
    unittest.main()
