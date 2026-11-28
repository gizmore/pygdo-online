# pygdo-online
Show how many users are online on a pygdo website.

Presence is held in Redis as a sorted set of primary user IDs and their latest
activity time. Activity refreshes this index even when database writes are
throttled. The first read after Redis starts warms it from the durable user
setting; if Redis is unavailable, the module falls back to the SQL query.
Both users and guests use a six-minute activity window.

Anonymous HTTP visitors are counted separately after they return the existing
session cookie probe. Redis stores only the session ID and recent activity,
not the cookie token; visitors are removed from the guest count upon login.
Guests expire using the same activity window as users. If Redis is unavailable,
the guest count is shown as unknown. The named-user roster excludes guests.
