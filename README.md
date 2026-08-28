# pygdo-online
Show how many users are online on a pygdo website.

Presence is held in Redis as a sorted set of primary user IDs and their
bucketed `last_activity` timestamp. The first read after Redis starts warms
that index once from the durable user setting; later page requests only query
Redis. If Redis is unavailable, the module falls back to the SQL query.
