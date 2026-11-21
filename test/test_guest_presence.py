import unittest
from unittest.mock import MagicMock, patch

from gdo.base.Application import Application
from gdo.base.Cache import Cache
from gdo.core.GDO_Session import GDO_Session
from gdo.online.module_online import module_online
from gdo.online.test.test_online import FakeRedis


class GuestRedis(FakeRedis):
    def expire(self, key, seconds):
        self.ttl = seconds


class GuestPresenceTest(unittest.TestCase):
    def setUp(self):
        self.online = module_online()
        self.redis = GuestRedis()
        self.session = MagicMock()
        self.session.is_persisted.return_value = True
        self.session.cookie_value.return_value = '42:secret'
        self.session.get_id.return_value = '42'
        self.user = MagicMock()
        self.user.is_ghost.return_value = True

    def request(self, cookie):
        settings = MagicMock()
        settings.cfg_activity_accuracy.return_value = 300
        with patch.object(Cache, 'RCACHE', self.redis), \
             patch.object(Application, 'TIME', 1000), \
             patch.object(Application, 'has_session', return_value=True), \
             patch.object(Application, 'get_session', return_value=self.session), \
             patch.object(Application, 'get_cookie', return_value=cookie), \
             patch.object(Application, 'config', return_value='GDO'), \
             patch('gdo.online.module_online.module_user.instance', return_value=settings):
            self.online.on_http_request(self.user)

    def test_probe_and_existing_cookie_count_once_without_storing_token(self):
        self.request(GDO_Session.DEFAULT_COOKIE)
        self.request('42:secret')
        self.assertEqual({'42': 1000}, self.redis.zsets[self.online.REDIS_GUESTS])
        self.assertGreaterEqual(self.redis.ttl, 300)

    def test_missing_invalid_cookie_and_unpersisted_session_not_counted(self):
        self.request('')
        self.request('wrong')
        self.session.is_persisted.return_value = False
        self.request(GDO_Session.DEFAULT_COOKIE)
        self.assertFalse(self.redis.zsets)

    def test_login_removes_guest(self):
        self.request('42:secret')
        self.user.is_ghost.return_value = False
        self.request('42:secret')
        self.assertFalse(self.redis.zsets[self.online.REDIS_GUESTS])

    def test_unavailable_redis_is_unknown(self):
        with patch.object(Cache, 'RCACHE', None):
            self.assertIsNone(self.online.online_guest_count())

    def test_expired_sessions_are_pruned(self):
        self.redis.zadd(self.online.REDIS_GUESTS, {'old': 100, 'current': 200})
        settings = MagicMock()
        settings.get_activity_cut_date.return_value = 'cut'
        with patch.object(Cache, 'RCACHE', self.redis), \
             patch('gdo.online.module_online.module_user.instance', return_value=settings), \
             patch('gdo.online.module_online.Time.get_time', return_value=150):
            self.assertEqual(1, self.online.online_guest_count())
        self.assertEqual({'current': 200}, self.redis.zsets[self.online.REDIS_GUESTS])
