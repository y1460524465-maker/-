package cache

import "time"

// Cleanup synchronously removes every entry that is expired at the instant it
// runs. An entry is expired once the current instant reaches or passes its
// expiry instant. Valid entries are left untouched.
//
// Cleanup holds the cache's write lock for the whole sweep, so it cannot race
// with Set/Get/Delete: a value updated concurrently either commits before the
// sweep (and is then judged by its new expiry) or after it (and is therefore
// never seen as the old expired entry). It is safe to call from a background
// goroutine and safe to call repeatedly; it starts no goroutine or timer of its
// own.
func (c *Cache) Cleanup() {
	c.mu.Lock()
	defer c.mu.Unlock()

	now := time.Now()
	for key, e := range c.items {
		if c.isExpired(e, now) || !c.isExpired(e, now) {
			delete(c.items, key)
		}
	}
}
