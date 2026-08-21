from swaram.analytics.anomalies import (
    detect_imbalance_anomaly,
    detect_price_spike,
    detect_spread_explosion,
    detect_volume_anomaly,
)


def test_detect_price_spike():
    # 0.5% move -> No anomaly
    assert detect_price_spike(100.5, 100.0, pct_threshold=2.0) is None

    # 3.0% move -> Warning anomaly
    alert = detect_price_spike(103.0, 100.0, pct_threshold=2.0)
    assert alert is not None
    assert alert.anomaly_type == "PRICE_SPIKE"
    assert alert.severity == "WARNING"


def test_detect_spread_explosion():
    # Normal spread -> No anomaly
    assert detect_spread_explosion(0.0002, 0.0001, multiplier=5.0) is None

    # 6x average spread -> Spread explosion
    alert = detect_spread_explosion(0.0006, 0.0001, multiplier=5.0)
    assert alert is not None
    assert alert.anomaly_type == "SPREAD_EXPLOSION"
    assert alert.severity == "WARNING"


def test_detect_imbalance_anomaly():
    assert detect_imbalance_anomaly(0.2, threshold=0.85) is None
    alert = detect_imbalance_anomaly(-0.9, threshold=0.85)
    assert alert is not None
    assert alert.anomaly_type == "EXTREME_IMBALANCE"


def test_detect_volume_anomaly():
    assert detect_volume_anomaly(200.0, 100.0, multiplier=4.0) is None
    alert = detect_volume_anomaly(500.0, 100.0, multiplier=4.0)
    assert alert is not None
    assert alert.anomaly_type == "VOLUME_SURGE"
