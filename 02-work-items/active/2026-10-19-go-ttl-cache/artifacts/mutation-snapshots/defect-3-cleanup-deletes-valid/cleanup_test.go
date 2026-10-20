package cache

import (
	"fmt"
	"sync"
	"testing"
	"time"
)

// snapshotEntries copies the cache's internal entry table. Cleanup tests use it
// to prove that expired entries were physically removed from the map, not just
// hidden from Get.
func snapshotEntries(c *Cache) map[string]entry {
	c.mu.RLock()
	defer c.mu.RUnlock()

	entries := make(map[string]entry, len(c.items))
	for key, e := range c.items {
		entries[key] = e
	}
	return entries
}

// insertEntry installs e directly so tests can control the exact expiry instant
// without depending on wall-clock sleeps.
func insertEntry(c *Cache, key string, e entry) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.items == nil {
		c.items = make(map[string]entry)
	}
	c.items[key] = e
}

// readEntry returns the stored entry, failing the test if key is absent.
func readEntry(t *testing.T, c *Cache, key string) entry {
	t.Helper()

	c.mu.RLock()
	defer c.mu.RUnlock()

	e, ok := c.items[key]
	if !ok {
		t.Fatalf("internal entry %q missing, want present", key)
	}
	return e
}

func assertEntryAbsent(t *testing.T, c *Cache, key, context string) {
	t.Helper()

	c.mu.RLock()
	_, ok := c.items[key]
	c.mu.RUnlock()
	if ok {
		t.Fatalf("%s: internal entry %q still present, want physically deleted", context, key)
	}
}

func assertEntryPresent(t *testing.T, c *Cache, key, context string) {
	t.Helper()

	c.mu.RLock()
	_, ok := c.items[key]
	c.mu.RUnlock()
	if !ok {
		t.Fatalf("%s: internal entry %q missing, want retained", context, key)
	}
}

func waitGroupTimeout(t *testing.T, wg *sync.WaitGroup, timeout time.Duration) {
	t.Helper()

	done := make(chan struct{})
	go func() {
		wg.Wait()
		close(done)
	}()

	select {
	case <-done:
	case <-time.After(timeout):
		t.Fatalf("concurrent operations did not finish within %v; possible deadlock", timeout)
	}
}

func TestCleanupZeroValueAndEmptyCache(t *testing.T) {
	var c Cache

	// The zero value has a nil map; Cleanup must tolerate that and be repeatable.
	c.Cleanup()
	c.Cleanup()

	if got := len(snapshotEntries(&c)); got != 0 {
		t.Fatalf("zero-value cache holds %d internal entries after Cleanup, want 0", got)
	}
	if v, ok := c.Get("missing"); ok || v != nil {
		t.Fatalf("Get(missing) = (%v, %v), want (nil, false)", v, ok)
	}
}

func TestCleanupRemovesOnlyExpiredEntries(t *testing.T) {
	c := new(Cache)
	now := time.Now()

	// Direct insertion pins the expiry instants. "expired-before-cleanup" uses
	// the captured now and Cleanup necessarily runs after that capture, so this
	// exercises the expired side; the exact now == expiresAt rule is covered by
	// TestIsExpiredBoundary.
	insertEntry(c, "expired-past", entry{val: "past", expiresAt: now.Add(-time.Hour)})
	insertEntry(c, "expired-before-cleanup", entry{val: "boundary", expiresAt: now})
	insertEntry(c, "valid-future", entry{val: "future", expiresAt: now.Add(time.Hour)})

	// Also exercise the public Set path for a valid entry.
	c.Set("valid-set", "fresh", time.Minute)

	// Preconditions: all entries exist physically, expired ones are invisible
	// to Get, and valid ones are visible before Cleanup runs.
	for _, key := range []string{"expired-past", "expired-before-cleanup", "valid-future", "valid-set"} {
		assertEntryPresent(t, c, key, "before cleanup")
	}
	for _, key := range []string{"expired-past", "expired-before-cleanup"} {
		if v, ok := c.Get(key); ok || v != nil {
			t.Fatalf("precondition: Get(%s) = (%v, %v), want (nil, false)", key, v, ok)
		}
	}
	for key, want := range map[string]any{"valid-future": "future", "valid-set": "fresh"} {
		if v, ok := c.Get(key); !ok || v != want {
			t.Fatalf("precondition: Get(%s) = (%v, %v), want (%v, true)", key, v, ok, want)
		}
	}

	c.Cleanup()

	if got := len(snapshotEntries(c)); got != 2 {
		t.Fatalf("internal entry count after Cleanup = %d, want 2", got)
	}

	for _, key := range []string{"expired-past", "expired-before-cleanup"} {
		assertEntryAbsent(t, c, key, "mixed cleanup")
	}
	for _, key := range []string{"valid-future", "valid-set"} {
		assertEntryPresent(t, c, key, "mixed cleanup")
	}

	if v, ok := c.Get("valid-future"); !ok || v != "future" {
		t.Fatalf("Get(valid-future) = (%v, %v), want (future, true)", v, ok)
	}
	if v, ok := c.Get("valid-set"); !ok || v != "fresh" {
		t.Fatalf("Get(valid-set) = (%v, %v), want (fresh, true)", v, ok)
	}
}

func TestCleanupAllExpired(t *testing.T) {
	c := new(Cache)
	now := time.Now()

	for i := 0; i < 5; i++ {
		key := fmt.Sprintf("expired-%d", i)
		insertEntry(c, key, entry{val: i, expiresAt: now.Add(-time.Minute)})
	}
	for i := 0; i < 5; i++ {
		assertEntryPresent(t, c, fmt.Sprintf("expired-%d", i), "all-expired setup")
	}

	c.Cleanup()

	if got := len(snapshotEntries(c)); got != 0 {
		t.Fatalf("internal entry count after cleaning all-expired cache = %d, want 0", got)
	}
	for i := 0; i < 5; i++ {
		assertEntryAbsent(t, c, fmt.Sprintf("expired-%d", i), "all-expired cleanup")
	}

	// Repeating Cleanup on an empty cache changes nothing.
	c.Cleanup()
	if got := len(snapshotEntries(c)); got != 0 {
		t.Fatalf("internal entry count after repeated Cleanup = %d, want 0", got)
	}
}

func TestCleanupKeepsAllValidEntriesAndIsIdempotent(t *testing.T) {
	c := new(Cache)
	c.Set("string", "value", time.Minute)
	c.Set("nil", nil, time.Minute)
	c.Set("", "empty-key", time.Minute)

	before := snapshotEntries(c)
	c.Cleanup()
	c.Cleanup()
	after := snapshotEntries(c)

	if len(after) != len(before) {
		t.Fatalf("valid entry count after Cleanup = %d, want %d", len(after), len(before))
	}
	for key, want := range before {
		got, ok := after[key]
		if !ok {
			t.Fatalf("valid entry %q was removed by Cleanup", key)
		}
		if got.val != want.val || !got.expiresAt.Equal(want.expiresAt) {
			t.Fatalf("valid entry %q changed by Cleanup: got (%v, %v), want (%v, %v)",
				key, got.val, got.expiresAt, want.val, want.expiresAt)
		}
	}

	if v, ok := c.Get("nil"); !ok || v != nil {
		t.Fatalf("Get(nil) after Cleanup = (%v, %v), want (nil, true)", v, ok)
	}
	if v, ok := c.Get(""); !ok || v != "empty-key" {
		t.Fatalf("Get(\"\") after Cleanup = (%v, %v), want (empty-key, true)", v, ok)
	}
}

func TestCleanupDoesNotResurrectNonPositiveTTLEntries(t *testing.T) {
	c := new(Cache)

	c.Set("zero", "old", time.Hour)
	if v, ok := c.Get("zero"); !ok || v != "old" {
		t.Fatalf("precondition: Get(zero) = (%v, %v), want (old, true)", v, ok)
	}
	c.Set("zero", "new", 0)
	assertEntryAbsent(t, c, "zero", "ttl=0 immediate")

	c.Set("negative", "old", time.Hour)
	if v, ok := c.Get("negative"); !ok || v != "old" {
		t.Fatalf("precondition: Get(negative) = (%v, %v), want (old, true)", v, ok)
	}
	c.Set("negative", "new", -time.Second)
	assertEntryAbsent(t, c, "negative", "ttl<0 immediate")

	c.Cleanup()

	assertEntryAbsent(t, c, "zero", "ttl=0 cleanup")
	assertEntryAbsent(t, c, "negative", "ttl<0 cleanup")
	if v, ok := c.Get("zero"); ok || v != nil {
		t.Fatalf("Get(zero) after Cleanup = (%v, %v), want (nil, false)", v, ok)
	}
	if v, ok := c.Get("negative"); ok || v != nil {
		t.Fatalf("Get(negative) after Cleanup = (%v, %v), want (nil, false)", v, ok)
	}

	// A later valid write must still work after cleanup.
	c.Set("zero", "revived", time.Minute)
	c.Cleanup()

	assertEntryPresent(t, c, "zero", "valid write after ttl<=0")
	if v, ok := c.Get("zero"); !ok || v != "revived" {
		t.Fatalf("Get(zero) after valid Set = (%v, %v), want (revived, true)", v, ok)
	}
}

func TestCleanupKeepsConcurrentlyUpdatedValue(t *testing.T) {
	c := new(Cache)
	const iterations = 200
	now := time.Now()

	// Seed every key as already expired using exact expiry instants; no sleep is
	// needed to make the setup deterministic.
	for i := 0; i < iterations; i++ {
		key := fmt.Sprintf("shared-%d", i)
		insertEntry(c, key, entry{val: "expired", expiresAt: now.Add(-time.Hour)})
	}

	// Precondition: the setup really produced expired entries. Without this,
	// the concurrent phase below could not exercise a stale removal snapshot.
	for i := 0; i < iterations; i++ {
		key := fmt.Sprintf("shared-%d", i)
		if v, ok := c.Get(key); ok {
			t.Fatalf("setup: Get(%s) = (%v, true) after expiry, want miss", key, v)
		}
	}

	start := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(2 * iterations)
	for i := 0; i < iterations; i++ {
		key := fmt.Sprintf("shared-%d", i)
		want := fmt.Sprintf("fresh-%d", i)
		go func(key, want string) {
			defer wg.Done()
			<-start
			c.Cleanup()
		}(key, want)
		go func(key, want string) {
			defer wg.Done()
			<-start
			c.Set(key, want, time.Minute)
		}(key, want)
	}
	close(start)
	waitGroupTimeout(t, &wg, 10*time.Second)

	// The initial value was already expired, but whichever side wins the lock
	// first, the fresh write must still be present after both operations finish.
	for i := 0; i < iterations; i++ {
		key := fmt.Sprintf("shared-%d", i)
		want := fmt.Sprintf("fresh-%d", i)
		assertEntryPresent(t, c, key, "concurrent update")
		if v, ok := c.Get(key); !ok || v != want {
			t.Fatalf("Get(%s) after concurrent Cleanup/Set = (%v, %v), want (%v, true)",
				key, v, ok, want)
		}
	}
}

func TestCleanupConcurrentWithSetGetDelete(t *testing.T) {
	c := new(Cache)
	const (
		workers    = 8
		iterations = 300
	)

	// Phase 1 preconditions: stable is never touched by the workers and must
	// survive; shared is the same-key contention target.
	c.Set("stable", "stable-value", time.Hour)
	c.Set("shared", "seed", time.Hour)
	if v, ok := c.Get("stable"); !ok || v != "stable-value" {
		t.Fatalf("precondition: Get(stable) = (%v, %v), want (stable-value, true)", v, ok)
	}
	if v, ok := c.Get("shared"); !ok || v != "seed" {
		t.Fatalf("precondition: Get(shared) = (%v, %v), want (seed, true)", v, ok)
	}

	start := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(workers + 2)

	// Two goroutines clean concurrently with the workers.
	for i := 0; i < 2; i++ {
		go func() {
			defer wg.Done()
			<-start
			for n := 0; n < iterations; n++ {
				c.Cleanup()
			}
		}()
	}

	for w := 0; w < workers; w++ {
		go func(w int) {
			defer wg.Done()
			<-start
			for n := 0; n < iterations; n++ {
				key := fmt.Sprintf("k%d-%d", w, n%20)
				switch n % 4 {
				case 0:
					c.Set(key, n, time.Minute)
				case 1:
					c.Set(key, n, time.Nanosecond)
				case 2:
					c.Get(key)
				case 3:
					c.Delete(key)
				}

				// Exercise all four methods on the same key as well.
				switch (w + n) % 4 {
				case 0:
					c.Set("shared", w, time.Minute)
				case 1:
					c.Set("shared", w, time.Nanosecond)
				case 2:
					c.Get("shared")
				case 3:
					c.Delete("shared")
				}
				c.Get("stable")
			}
		}(w)
	}

	close(start)
	waitGroupTimeout(t, &wg, 10*time.Second)

	// Phase 2 postconditions after quiescence.
	if v, ok := c.Get("stable"); !ok || v != "stable-value" {
		t.Fatalf("postcondition: Get(stable) = (%v, %v), want (stable-value, true)", v, ok)
	}

	c.Set("final", "done", time.Minute)
	c.Cleanup()
	assertEntryPresent(t, c, "final", "after concurrent operations")
	if v, ok := c.Get("final"); !ok || v != "done" {
		t.Fatalf("Get(final) after concurrent operations = (%v, %v), want (done, true)", v, ok)
	}

	// Expired entries stay hidden and are physically removed by Cleanup, even
	// after the concurrent phase.
	insertEntry(c, "expired-after", entry{val: "stale", expiresAt: time.Now().Add(-time.Nanosecond)})
	if v, ok := c.Get("expired-after"); ok || v != nil {
		t.Fatalf("Get(expired-after) = (%v, %v), want (nil, false)", v, ok)
	}
	c.Cleanup()
	assertEntryAbsent(t, c, "expired-after", "post-concurrency cleanup")
}
