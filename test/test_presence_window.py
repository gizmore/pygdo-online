from unittest.mock import MagicMock, patch
from redis.exceptions import RedisError

from gdotest.TestUtil import GDOTestCase
from gdo.base.Application import Application
from gdo.base.Cache import Cache
from gdo.online.module_online import module_online
from gdo.online.test.test_online import FakeRedis


class PresenceWindowTest(GDOTestCase):
    def test_failed_warmup_does_not_mark_index_ready(self):
        online = module_online()
        redis = FakeRedis()
        user = MagicMock()
        user.get_setting_val.return_value = '800'
        with patch.object(Cache, 'RCACHE', redis), \
             patch.object(redis, 'zadd', side_effect=RedisError('unavailable')), \
             patch.object(online, 'online_users_sql', return_value=[user]), \
             patch('gdo.online.module_online.Time.get_time', return_value=800):
            self.assertIsNone(online.online_users_redis('640'))
            self.assertFalse(redis.exists(online.REDIS_READY))

    def test_first_event_does_not_skip_warmup_and_refresh_never_moves_backwards(self):
        online = module_online()
        redis = FakeRedis()
        user = MagicMock()
        user.gdo_val.return_value = None
        user.get_id.return_value = '42'
        user.get_setting_val.return_value = '800'
        with patch.object(Cache, 'RCACHE', redis), \
             patch.object(online, 'online_users_sql', return_value=[user]) as sql, \
             patch('gdo.online.module_online.Time.get_time', side_effect=lambda value: float(value)), \
             patch('gdo.online.module_online.module_user.instance') as provider:
            provider.return_value.cfg_activity_accuracy.return_value = 300
            online.on_presence_seen(user, 1000)
            self.assertFalse(redis.exists(online.REDIS_READY))
            self.assertEqual([user], online.online_users_redis('640'))
            self.assertEqual(1000, redis.zsets[online.REDIS_USERS]['42'])
            self.assertTrue(redis.exists(online.REDIS_READY))
            sql.assert_called_once()

    def test_recent_presence_survives_and_expires_after_cutoff(self):
        online = module_online()
        redis = FakeRedis()
        user = MagicMock()
        user.gdo_val.return_value = None
        user.get_id.return_value = '42'
        with patch.object(Cache, 'RCACHE', redis), \
             patch('gdo.online.module_online.GDO_User.table') as table, \
             patch('gdo.online.module_online.Time.get_time', side_effect=lambda value: float(value)):
            table.return_value.get_by_aid.return_value = user
            redis.set(online.REDIS_READY, '1')
            online.on_presence_seen(user, 1000)
            self.assertEqual([user], online.online_users_redis('640'))
            online.on_presence_seen(user, 1200)
            self.assertEqual([user], online.online_users_redis('1001'))
            self.assertEqual([], online.online_users_redis('1201'))
