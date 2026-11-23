import unittest
from unittest.mock import MagicMock, patch

from redis.exceptions import RedisError
from gdo.base.Cache import Cache
from gdo.online.module_online import module_online


class OnlineCountCacheTest(unittest.TestCase):
    def setUp(self):
        self.online = module_online()
        self.online.online_users = MagicMock(return_value=[1, 2])
        self.online.online_guest_count = MagicMock(return_value=1)

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
