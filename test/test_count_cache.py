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
        for name, default in (('online_refresh_interval', '20s'), ('online_count_cache_duration', '4s 777ms')):
            self.assertIsInstance(fields[name], GDT_Duration)
            self.assertEqual(default, fields[name].get_initial())
        with patch('gdo.base.Application.Application.get_mode', return_value=None):
            user_setting = module_online().gdo_user_settings()[0]
        self.assertIsInstance(user_setting, GDT_Duration)
        self.assertEqual('10s', user_setting.get_initial())

    def test_guest_and_member_refresh_intervals(self):
        user = MagicMock()
        user.is_ghost.return_value = True
        self.online.get_config_value.return_value = 20
        self.assertEqual(20, self.online.refresh_interval(user))
        user.is_ghost.return_value = False
        user.is_type.return_value = True
        self.assertEqual(20, self.online.refresh_interval(user))
        user.is_type.return_value = False
        user.get_setting_value.return_value = 5
        self.assertEqual(5, self.online.refresh_interval(user))
        user.get_setting_value.assert_called_once_with('online_user_refresh_interval')

    def setUp(self):
        self.online = module_online()
        self.online.online_users = MagicMock(return_value=[1, 2])
        self.online.online_guest_count = MagicMock(return_value=1)
        self.online.get_config_value = MagicMock(return_value=4.777)

    def test_cache_hit_avoids_recount(self):
        redis = MagicMock()
        redis.get.return_value = b'{"users": 4, "guests": 2, "stream_viewers": 3}'
        with patch.object(Cache, 'RCACHE', redis):
            self.assertEqual({'users': 4, 'guests': 2, 'stream_viewers': 3}, self.online.online_counts())
        self.online.online_users.assert_not_called()
        self.online.online_guest_count.assert_not_called()

    def test_cache_miss_is_shared_with_expiry(self):
        redis = MagicMock()
        redis.get.return_value = None
        with patch.object(Cache, 'RCACHE', redis):
            self.assertEqual({'users': 2, 'guests': 1, 'stream_viewers': None}, self.online.online_counts())
        redis.set.assert_called_once_with(self.online.REDIS_COUNT, '{"users": 2, "guests": 1, "stream_viewers": null}', px=4777)

    def test_configured_cache_duration_is_used(self):
        redis = MagicMock()
        redis.get.return_value = None
        self.online.get_config_value.return_value = 27
        with patch.object(Cache, 'RCACHE', redis):
            self.online.online_counts()
        self.assertEqual(27000, redis.set.call_args.kwargs['px'])

    def test_redis_failure_falls_back_to_count(self):
        redis = MagicMock()
        redis.get.side_effect = RedisError('unavailable')
        redis.set.side_effect = RedisError('unavailable')
        with patch.object(Cache, 'RCACHE', redis):
            self.assertEqual({'users': 2, 'guests': 1, 'stream_viewers': None}, self.online.online_counts())

    def test_no_redis_keeps_unknown_guest_count(self):
        self.online.online_guest_count.return_value = None
        with patch.object(Cache, 'RCACHE', None):
            self.assertEqual({'users': 2, 'guests': None, 'stream_viewers': None}, self.online.online_counts())

    def test_viewer_count_read_and_invalid_or_expired(self):
        redis = MagicMock()
        with patch.object(Cache, 'RCACHE', redis):
            for raw, expected in ((b'3', 3), (b'0', 0), (None, None), (b'17', None), (b'no', None)):
                redis.get.return_value = raw
                self.assertEqual(expected, self.online.stream_viewer_count())
