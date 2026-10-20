package cache

import (
	"fmt"
	"sync"
	"testing"
	"time"
)

func TestZeroValueCache(t *testing.T) {
	var c Cache

	if v, ok := c.Get("missing"); ok || v != nil {
		t.Fatalf("zero-value Get(missing) = (%v, %v), want (nil, false)", v, ok)
	}

	c.Set("key", "value", time.Minute)
	if v, ok := c.Get("key"); !ok || v != "value" {
		t.Fatalf("Get(key) = (%v, %v), want (value, true)", v, ok)
	}

	c.Delete("key")
	if v, ok := c.Get("key"); ok || v != nil {
		t.Fatalf("Get after Delete = (%v, %v), want (nil, false)", v, ok)
	}
}

func TestMissingAndEmptyKey(t *testing.T) {
	c := new(Cache)

	if v, ok := c.Get("missing"); ok || v != nil {
		t.Fatalf("Get(missing) = (%v, %v), want (nil, false)", v, ok)
	}

	c.Set("", "empty-key", time.Minute)
	if v, ok := c.Get(""); !ok || v != "empty-key" {
		t.Fatalf("Get(empty key) = (%v, %v), want (empty-key, true)", v, ok)
	}

	// Deleting a missing key is idempotent and must not disturb other entries.
	c.Set("kept", "value", time.Minute)
	c.Delete("never-existed")
	c.Delete("never-existed")
	if v, ok := c.Get("kept"); !ok || v != "value" {
		t.Fatalf("Get(kept) after deleting missing keys = (%v, %v), want (value, true)", v, ok)
	}

	c.Delete("")
	if v, ok := c.Get(""); ok || v != nil {
		t.Fatalf("Get(empty key) after Delete = (%v, %v), want (nil, false)", v, ok)
	}
}

func TestNilValueIsAHit(t *testing.T) {
	c := new(Cache)
	c.Set("nil-key", nil, time.Minute)

	v, ok := c.Get("nil-key")
	if !ok {
		t.Fatal("Get(nil-key) reported a miss, want a hit")
	}
	if v != nil {
		t.Fatalf("Get(nil-key) = %v, want nil", v)
	}

	if v, ok := c.Get("missing"); ok || v != nil {
		t.Fatalf("Get(missing) = (%v, %v), want (nil, false)", v, ok)
	}
}

func TestSetOverwritesValueAndTTL(t *testing.T) {
	c := new(Cache)

	// Replacing the value keeps a single entry holding the newest value.
	c.Set("value-key", "first", time.Hour)
	c.Set("value-key", "second", time.Hour)
	if v, ok := c.Get("value-key"); !ok || v != "second" {
		t.Fatalf("Get(value-key) = (%v, %v), want (second, true)", v, ok)
	}

	// Replacing an already expired entry with a positive TTL must revive it:
	// Set has to overwrite the stored expiry, not just the value.
	now := time.Now()
	insertEntry(c, "ttl-key", entry{val: "old", expiresAt: now.Add(-time.Hour)})
	if v, ok := c.Get("ttl-key"); ok || v != nil {
		t.Fatalf("precondition: Get(ttl-key) = (%v, %v), want expired (nil, false)", v, ok)
	}

	c.Set("ttl-key", "new", time.Hour)
	e := readEntry(t, c, "ttl-key")
	if e.val != "new" {
		t.Fatalf("ttl-key stored value = %v, want new", e.val)
	}
	if e.expiresAt.Before(now.Add(time.Hour)) {
		t.Fatalf("ttl-key expiresAt = %v, want a fresh expiry at or after %v", e.expiresAt, now.Add(time.Hour))
	}
	if v, ok := c.Get("ttl-key"); !ok || v != "new" {
		t.Fatalf("Get(ttl-key) after revive = (%v, %v), want (new, true)", v, ok)
	}

	// A later Set with a different positive TTL replaces the previous expiry.
	c.Set("ttl-key", "newer", 2*time.Hour)
	e2 := readEntry(t, c, "ttl-key")
	if e2.val != "newer" {
		t.Fatalf("ttl-key stored value after second Set = %v, want newer", e2.val)
	}
	if !e2.expiresAt.After(e.expiresAt) {
		t.Fatalf("ttl-key expiresAt after second Set = %v, want later than %v", e2.expiresAt, e.expiresAt)
	}
	if v, ok := c.Get("ttl-key"); !ok || v != "newer" {
		t.Fatalf("Get(ttl-key) after second Set = (%v, %v), want (newer, true)", v, ok)
	}
}

func TestNonPositiveTTLExpiresImmediately(t *testing.T) {
	c := new(Cache)

	c.Set("zero", "old", time.Hour)
	if v, ok := c.Get("zero"); !ok || v != "old" {
		t.Fatalf("precondition: Get(zero) = (%v, %v), want (old, true)", v, ok)
	}
	c.Set("zero", "new", 0)
	if v, ok := c.Get("zero"); ok || v != nil {
		t.Fatalf("Get(zero) after ttl=0 = (%v, %v), want (nil, false)", v, ok)
	}
	if _, present := snapshotEntries(c)["zero"]; present {
		t.Fatal("ttl=0 left the old entry physically stored, want it removed")
	}

	c.Set("negative", "old", time.Hour)
	if v, ok := c.Get("negative"); !ok || v != "old" {
		t.Fatalf("precondition: Get(negative) = (%v, %v), want (old, true)", v, ok)
	}
	c.Set("negative", "new", -time.Nanosecond)
	if v, ok := c.Get("negative"); ok || v != nil {
		t.Fatalf("Get(negative) after ttl<0 = (%v, %v), want (nil, false)", v, ok)
	}
	if _, present := snapshotEntries(c)["negative"]; present {
		t.Fatal("ttl<0 left the old entry physically stored, want it removed")
	}

	c.Set("absent-zero", "value", 0)
	if v, ok := c.Get("absent-zero"); ok || v != nil {
		t.Fatalf("Get(absent-zero) = (%v, %v), want (nil, false)", v, ok)
	}

	c.Set("absent-negative", "value", -time.Hour)
	if v, ok := c.Get("absent-negative"); ok || v != nil {
		t.Fatalf("Get(absent-negative) = (%v, %v), want (nil, false)", v, ok)
	}

	c.Set("zero", "valid", time.Minute)
	if v, ok := c.Get("zero"); !ok || v != "valid" {
		t.Fatalf("Get(zero) after valid Set = (%v, %v), want (valid, true)", v, ok)
	}
}

func TestExpiryHidesValue(t *testing.T) {
	c := new(Cache)
	now := time.Now()

	// Internal expiry instants make this deterministic; no sleep is involved.
	insertEntry(c, "valid", entry{val: "value", expiresAt: now.Add(time.Hour)})
	insertEntry(c, "expired", entry{val: "stale", expiresAt: now.Add(-time.Nanosecond)})

	if v, ok := c.Get("valid"); !ok || v != "value" {
		t.Fatalf("Get(valid) = (%v, %v), want (value, true)", v, ok)
	}
	if v, ok := c.Get("expired"); ok || v != nil {
		t.Fatalf("Get(expired) = (%v, %v), want (nil, false)", v, ok)
	}

	// The entry captured exactly at now is necessarily in the past by the time
	// Get calls time.Now; the exact equal-to-expiresAt rule is covered by
	// TestIsExpiredBoundary.
	insertEntry(c, "at-capture", entry{val: "boundary", expiresAt: now})
	if v, ok := c.Get("at-capture"); ok || v != nil {
		t.Fatalf("Get(at-capture) = (%v, %v), want (nil, false)", v, ok)
	}
}

func TestIsExpiredBoundary(t *testing.T) {
	c := new(Cache)
	expiresAt := time.Now()
	e := entry{val: "value", expiresAt: expiresAt}

	tests := []struct {
		name string
		now  time.Time
		want bool
	}{
		{name: "one nanosecond before", now: expiresAt.Add(-time.Nanosecond), want: false},
		{name: "exactly at expiresAt", now: expiresAt, want: true},
		{name: "one nanosecond after", now: expiresAt.Add(time.Nanosecond), want: true},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			if got := c.isExpired(e, tc.now); got != tc.want {
				t.Fatalf("isExpired at %v = %v, want %v", tc.now, got, tc.want)
			}
		})
	}
}

func TestConcurrentZeroValueInitialization(t *testing.T) {
	var c Cache
	const (
		goroutines   = 16
		perGoroutine = 50
	)

	start := make(chan struct{})
	var wg sync.WaitGroup
	wg.Add(goroutines)
	for i := 0; i < goroutines; i++ {
		go func(i int) {
			defer wg.Done()
			<-start
			for j := 0; j < perGoroutine; j++ {
				c.Set(fmt.Sprintf("g%d-k%d", i, j), j, time.Minute)
			}
		}(i)
	}

	close(start)
	wg.Wait()

	for i := 0; i < goroutines; i++ {
		for j := 0; j < perGoroutine; j++ {
			key := fmt.Sprintf("g%d-k%d", i, j)
			v, ok := c.Get(key)
			if !ok {
				t.Fatalf("Get(%s) missed after concurrent Set", key)
			}
			if v != j {
				t.Fatalf("Get(%s) = %v, want %d", key, v, j)
			}
		}
	}
}

func TestConcurrentAllMethodsSameKey(t *testing.T) {
	c := new(Cache)
	const (
		workers    = 8
		iterations = 200
	)

	// Phase 1 preconditions: an untouched key and the contended key are visible.
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
	wg.Add(workers)
	for w := 0; w < workers; w++ {
		go func(w int) {
			defer wg.Done()
			<-start
			privateKey := fmt.Sprintf("worker-%d", w)
			for n := 0; n < iterations; n++ {
				// "shared" is the same-key contention target for all four
				// methods; Cleanup also sweeps it because it holds the lock.
				switch (w + n) % 4 {
				case 0:
					c.Set("shared", fmt.Sprintf("w%d-%d", w, n), time.Minute)
				case 1:
					c.Get("shared")
					c.Get("stable")
				case 2:
					c.Delete("shared")
				case 3:
					c.Cleanup()
				}

				// Only this goroutine touches privateKey, so this mid-flight
				// assertion is deterministic even while "shared" is contended.
				c.Set(privateKey, n, time.Minute)
				if v, ok := c.Get(privateKey); !ok || v != n {
					t.Errorf("worker %d iteration %d: Get(%s) = (%v, %v), want (%d, true)",
						w, n, privateKey, v, ok, n)
				}
			}
		}(w)
	}

	close(start)
	waitGroupTimeout(t, &wg, 10*time.Second)

	// Phase 2 postconditions after quiescence: the untouched key still has its
	// original value and every private-key last write is visible.
	if v, ok := c.Get("stable"); !ok || v != "stable-value" {
		t.Fatalf("postcondition: Get(stable) = (%v, %v), want (stable-value, true)", v, ok)
	}
	for w := 0; w < workers; w++ {
		key := fmt.Sprintf("worker-%d", w)
		if v, ok := c.Get(key); !ok || v != iterations-1 {
			t.Fatalf("postcondition: Get(%s) = (%v, %v), want (%d, true)",
				key, v, ok, iterations-1)
		}
	}

	// Expired entries stay hidden until Cleanup physically removes them.
	insertEntry(c, "expired-after", entry{val: "stale", expiresAt: time.Now().Add(-time.Nanosecond)})
	if v, ok := c.Get("expired-after"); ok || v != nil {
		t.Fatalf("Get(expired-after) = (%v, %v), want (nil, false)", v, ok)
	}
	c.Cleanup()
	assertEntryAbsent(t, c, "expired-after", "post-concurrency cleanup")

	c.Set("final", "done", time.Minute)
	if v, ok := c.Get("final"); !ok || v != "done" {
		t.Fatalf("Get(final) = (%v, %v), want (done, true)", v, ok)
	}
	c.Delete("final")
	if v, ok := c.Get("final"); ok || v != nil {
		t.Fatalf("Get(final) after Delete = (%v, %v), want (nil, false)", v, ok)
	}
}
