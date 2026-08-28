import os
import unittest
from unittest.mock import patch

from gdo.base.Application import Application
from gdo.base.Cache import Cache
from gdo.base.ModuleLoader import ModuleLoader
from gdo.online.module_online import module_online
from gdotest.TestUtil import web_plug, WebPlug, GDOTestCase, install_module


class FakeRedis:
    """The tiny Redis-ZSET surface used by the online-presence index."""

    def __init__(self):
        self.values = {}
        self.zsets = {}

    def exists(self, key):
        return int(key in self.values or bool(self.zsets.get(key)))

    def get(self, key):
        return None

    def set(self, key, value, ex=None):
        self.values[key] = value

    def delete(self, *keys):
        for key in keys:
            self.values.pop(key, None)
            self.zsets.pop(key, None)

    def zadd(self, key, values):
        self.zsets.setdefault(key, {}).update(values)

    def zrem(self, key, member):
        self.zsets.get(key, {}).pop(member, None)

    def zremrangebyscore(self, key, minimum, maximum):
        exclusive = str(maximum).startswith('(')
        maximum = float(str(maximum).lstrip('('))
        for member, score in list(self.zsets.get(key, {}).items()):
            if score < maximum or (not exclusive and score <= maximum):
                del self.zsets[key][member]

    def zrangebyscore(self, key, minimum, maximum):
        minimum = float(minimum)
        return [member for member, score in self.zsets.get(key, {}).items()
                if minimum <= score]


class OnlineUsersTest(GDOTestCase):

    def setUp(self):
        super().setUp()
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        loader = ModuleLoader.instance()
        loader.load_modules_db(True)
        install_module('online')
        loader.init_modules(True, True)
        module_online.instance().on_clear_cache()
        WebPlug.COOKIES = {}

    def test_01_online_users(self):
        web_plug('core.welcome.html').user('gizmore').exec()
        web_plug('core.welcome.html').user('gizmore').exec()
        out = web_plug('core.welcome.html').user('gizmore').exec()
        self.assertIn('Users Online', out, 'Online users broken')

    def test_02_redis_presence_warms_once_then_avoids_sql(self):
        web_plug('core.welcome.html').user('gizmore').exec()
        online = module_online.instance()
        with patch.object(Cache, 'RCACHE', FakeRedis()), \
             patch.object(online, 'online_users_sql', wraps=online.online_users_sql) as sql:
            self.assertTrue(online.online_users())
            self.assertTrue(online.online_users())
            self.assertEqual(1, sql.call_count)


if __name__ == '__main__':
    unittest.main()
