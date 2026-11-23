import unittest
from unittest.mock import MagicMock, patch

from redis.exceptions import RedisError
from gdo.base.Cache import Cache
from gdo.online.module_online import module_online
from gdo.date.GDT_Duration import GDT_Duration


class OnlineCountCacheTest(unittest.TestCase):
    def test_intervals_are_duration_settings_with_expected_defaults(self):
        with patch('gdo.base.Application.Application.get_mode', return_value=None):
            fields = {field.get_name(): field for field in module_online().gdo_module_config()}
        for name, default in (('online_refresh_interval', '11s'), ('online_count_cache_duration', '10s')):
            self.assertIsInstance(fields[name], GDT_Duration)
            self.assertEqual(default, fields[name].get_initial())

    def setUp(self):
        self.online = module_online()
        self.online.online_users = MagicMock(return_value=[1, 2])
        self.online.online_guest_count = MagicMock(return_value=1)
        self.online.get_config_value = MagicMock(return_value=10)

    def test_cache_hit_avoids_recount(self):
        redis = MagicMock()
        redis.get.return_value = b'{"users": 4, "guests": 2}'
        with patch.object(Cache, 'RCACHE', redis):
            self.assertEqual({'users': 4, 'guests': 2}, self.online.online_counts())
        self.online.online_users.assert_not_called()
        self.online.online_guest_count.assert_not_called()

    def test_cache_miss_is_shared_with_expiry(self):
        redis = MagicMock()
        redis.get.return_value = None
        with patch.object(Cache, 'RCACHE', redis):
            self.assertEqual({'users': 2, 'guests': 1}, self.online.online_counts())
        redis.set.assert_called_once_with(self.online.REDIS_COUNT, '{"users": 2, "guests": 1}', ex=10)

    def test_configured_cache_duration_is_used(self):
        redis = MagicMock()
        redis.get.return_value = None
        self.online.get_config_value.return_value = 27
        with patch.object(Cache, 'RCACHE', redis):
            self.online.online_counts()
        self.assertEqual(27, redis.set.call_args.kwargs['ex'])

    def test_redis_failure_falls_back_to_count(self):
        redis = MagicMock()
        redis.get.side_effect = RedisError('unavailable')
        redis.set.side_effect = RedisError('unavailable')
        with patch.object(Cache, 'RCACHE', redis):
            self.assertEqual({'users': 2, 'guests': 1}, self.online.online_counts())

    def test_no_redis_keeps_unknown_guest_count(self):
        self.online.online_guest_count.return_value = None
        with patch.object(Cache, 'RCACHE', None):
            self.assertEqual({'users': 2, 'guests': None}, self.online.online_counts())
