"""Rate-limiter is puur (tijd komt binnen als parameter) en dus DB-vrij testbaar."""
from app.ratelimit import RateLimiter


def test_laat_toe_tot_de_limiet_en_blokkeert_daarna():
    rl = RateLimiter(max_per_window=3, window_seconds=60.0)
    assert [rl.toegestaan("ip", nu) for nu in (0.0, 0.1, 0.2)] == [True, True, True]
    assert rl.toegestaan("ip", 0.3) is False


def test_venster_schuift_op():
    rl = RateLimiter(max_per_window=2, window_seconds=60.0)
    assert rl.toegestaan("ip", 0.0) is True
    assert rl.toegestaan("ip", 1.0) is True
    assert rl.toegestaan("ip", 2.0) is False
    # 61s na de eerste tik is die vervallen → weer ruimte.
    assert rl.toegestaan("ip", 61.0) is True


def test_ip_s_zijn_onafhankelijk():
    rl = RateLimiter(max_per_window=1, window_seconds=60.0)
    assert rl.toegestaan("ip-a", 0.0) is True
    assert rl.toegestaan("ip-b", 0.0) is True
    assert rl.toegestaan("ip-a", 0.1) is False
