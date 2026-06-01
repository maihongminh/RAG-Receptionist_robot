from app.auth.rate_limiter import InMemoryRateLimiter


def test_rate_limiter_blocks_after_max_attempts():
    limiter = InMemoryRateLimiter()

    assert limiter.allow("client", max_attempts=2, window_seconds=60)
    assert limiter.allow("client", max_attempts=2, window_seconds=60)
    assert not limiter.allow("client", max_attempts=2, window_seconds=60)


def test_rate_limiter_uses_separate_keys():
    limiter = InMemoryRateLimiter()

    assert limiter.allow("client-a", max_attempts=1, window_seconds=60)
    assert not limiter.allow("client-a", max_attempts=1, window_seconds=60)
    assert limiter.allow("client-b", max_attempts=1, window_seconds=60)
