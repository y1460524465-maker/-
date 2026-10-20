// Package cache provides a concurrency-safe in-memory key/value cache whose
// entries expire after a configurable time-to-live.
package cache

import (
	"sync"
	"time"
)

// entry is a value together with the instant at which it stops being visible.
type entry struct {
	val       any
	expiresAt time.Time
}

// Cache is a concurrency-safe in-memory cache. Its zero value is ready to use.
//
// A Cache must not be copied after first use.
type Cache struct {
	mu    sync.RWMutex
	items map[string]entry
}

// Set stores val under key and replaces any previous value. A positive ttl is
// measured from this call; a ttl less than or equal to zero removes key
// immediately so that any previous value is no longer visible.
func (c *Cache) Set(key string, val any, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if ttl <= 0 {
		delete(c.items, key)
		return
	}
	if c.items == nil {
		c.items = make(map[string]entry)
	}
	c.items[key] = entry{
		val:       val,
		expiresAt: time.Now().Add(ttl),
	}
}

// Get returns the value stored under key and whether it is currently visible.
// Missing and expired entries return (nil, false); a visible nil value returns
// (nil, true). Expired entries are hidden without being removed from the map.
func (c *Cache) Get(key string) (any, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	e, ok := c.items[key]
	if !ok {
		return nil, false
	}
	if c.isExpired(e, time.Now()) {
		return nil, false
	}
	return e.val, true
}

// Delete removes key. Deleting a missing key is a no-op and is safe to repeat.
func (c *Cache) Delete(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()

	delete(c.items, key)
}

// isExpired reports whether e is expired at now. An entry is expired once the
// current instant reaches or passes its expiry instant.
func (c *Cache) isExpired(e entry, now time.Time) bool {
	return !now.Before(e.expiresAt)
}
