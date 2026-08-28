from gdo.base.Application import Application
from gdo.base.Cache import Cache
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.Util import module_enabled
from gdo.base.util.href import href
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_Container import GDT_Container
from gdo.online.GDT_OnlinePanel import GDT_OnlinePanel
from gdo.ui.GDT_Page import GDT_Page
from gdo.ui.GDT_PageLocation import GDT_PageLocation
from gdo.ui.GDT_Link import GDT_Link
from gdo.user.module_user import module_user
from gdo.date.Time import Time

from redis.exceptions import RedisError


class module_online(GDO_Module):

    REDIS_USERS = 'online:users'
    REDIS_READY = 'online:users:ready'

    def __init__(self):
        super().__init__()
        self._priority = 40

    def gdo_friendencies(self) -> list:
        return [
            'maps',
        ]

    def gdo_module_config(self) -> list[GDT]:
        return [
            GDT_PageLocation('online_bar_location').not_null().initial('_bottom_bar'),
        ]

    def cfg_page_location(self) -> GDT_Container:
        return self.get_config_value('online_bar_location')

    def gdo_init(self):
        Application.EVENTS.subscribe('user_setting_last_activity_changed', self.on_last_activity_changed)
        Application.EVENTS.subscribe('user_logout', self.on_user_logout)

    def gdo_load_scripts(self, page: 'GDT_Page'):
        if module_enabled('maps'):
            self.add_js('js/pygdo-online-map.js')
            self.add_css('css/pygdo-online.css')

    def on_last_activity_changed(self, user: GDO_User, val):
        """Refresh a primary user's Redis presence entry.

        ``last_activity`` is deliberately bucketed by module_user.  Using the
        same timestamp as the sorted-set score preserves its online semantics
        while avoiding a database scan for every rendered page.
        """
        if user.gdo_val('user_link') is None:
            self.redis_set_online(user.get_id(), Time.get_time(val))

    async def on_user_logout(self, user: GDO_User):
        if user.gdo_val('user_link') is None:
            self.redis_remove_online(user.get_id())

    def on_clear_cache(self):
        """Forget the presence index; the next read warms it from SQL."""
        if redis := Cache.RCACHE:
            try:
                redis.delete(self.REDIS_USERS, self.REDIS_READY)
            except RedisError:
                pass

    @staticmethod
    def redis_enabled() -> bool:
        return Cache.RCACHE is not None

    def redis_ready_ttl(self) -> int:
        """Periodically re-warm after a Redis reset without per-request SQL."""
        return max(60, int(module_user.instance().cfg_activity_accuracy()) * 2)

    def redis_mark_ready(self):
        if redis := Cache.RCACHE:
            redis.set(self.REDIS_READY, b'1', ex=self.redis_ready_ttl())

    def redis_set_online(self, user_id: str, score: float):
        if redis := Cache.RCACHE:
            try:
                redis.zadd(self.REDIS_USERS, {str(user_id): score})
                # A marker distinguishes an intentionally empty index from
                # one that has not been warmed after Redis was cleared.
                self.redis_mark_ready()
            except RedisError:
                pass

    def redis_remove_online(self, user_id: str):
        if redis := Cache.RCACHE:
            try:
                redis.zrem(self.REDIS_USERS, str(user_id))
                self.redis_mark_ready()
            except RedisError:
                pass

    def online_users_sql(self, cut: str) -> list[GDO_User]:
        return [
            user for user in GDO_User.table().with_settings_result([('last_activity', '>=', cut)])
            if user.gdo_val('user_link') is None
        ]

    def online_users_redis(self, cut: str) -> list[GDO_User] | None:
        """Read online primary account ids from Redis, or ``None`` on failure."""
        redis = Cache.RCACHE
        if redis is None:
            return None
        try:
            if not redis.exists(self.REDIS_READY):
                # Redis has just started or was cleared: use the durable
                # setting once, then all later page requests are Redis-only.
                users = self.online_users_sql(cut)
                for user in users:
                    self.redis_set_online(user.get_id(), Application.TIME)
                self.redis_mark_ready()
                return users

            cut_score = Time.get_time(cut)
            redis.zremrangebyscore(self.REDIS_USERS, '-inf', f'({cut_score}')
            ids = redis.zrangebyscore(self.REDIS_USERS, cut_score, '+inf')
            users = []
            for user_id in ids:
                if isinstance(user_id, bytes):
                    user_id = user_id.decode()
                if (user := GDO_User.table().get_by_aid(str(user_id))) and user.gdo_val('user_link') is None:
                    users.append(user)
            return users
        except RedisError:
            return None

    def online_users(self) -> list[GDO_User]:
        """Return active primary accounts, not their linked connector identities."""
        cut = module_user.instance().get_activity_cut_date()
        if self.redis_enabled() and (users := self.online_users_redis(cut)) is not None:
            return users
        return self.online_users_sql(cut)

    def online_users_with_positions(self) -> list[dict]:
        """Return the current online users that have a stored map position."""
        from gdo.maps.GDO_UserPos import GDO_UserPos

        positions = {}
        for position in GDO_UserPos.table().select().order('up_created DESC').exec():
            positions.setdefault(position.gdo_val('up_user'), position)
        users = []
        for user in self.online_users():
            if position := positions.get(user.get_id()):
                users.append({
                    'name': user.get_name_sid(),
                    'profile_url': href('user', 'profile', f'&for={user.get_name_sid()}'),
                    'avatar': self.avatar_href(user),
                    'lat': float(position.gdo_val('up_pos_lat')),
                    'lng': float(position.gdo_val('up_pos_lng')),
                })
        return users

    @staticmethod
    def avatar_href(user: GDO_User) -> str | None:
        if not module_enabled('avatar'):
            return None
        from gdo.avatar.GDT_Avatar import GDT_Avatar
        return GDT_Avatar('avatar').for_user(user).href_render()

    def gdo_init_sidebar(self, page: 'GDT_Page'):
        """
        Put the who is online into a page bar.
        """
        self.cfg_page_location().add_field(GDT_OnlinePanel())
        if module_enabled('maps'):
            count = len(self.online_users())
            page._left_bar.add_field(GDT_Link().icon('map').href(self.href('map')).text('mt_online_map', (count,)))
