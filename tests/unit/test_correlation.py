import numpy as np
import pytest
from swaram.analytics.correlation import compute_correlation_matrix


def test_compute_correlation_matrix():
    # Perfectly correlated
    r1 = np.array([0.01, 0.02, -0.01, 0.03, -0.02], dtype=float)
    r2 = np.array([0.01, 0.02, -0.01, 0.03, -0.02], dtype=float)
    # Inverse correlated
    r3 = np.array([-0.01, -0.02, 0.01, -0.03, 0.02], dtype=float)

    returns = {"BTC": r1, "ETH": r2, "GOLD": r3}
    matrix = compute_correlation_matrix(returns)

    assert matrix["BTC"]["BTC"] == 1.0
    assert pytest.approx(matrix["BTC"]["ETH"], 0.01) == 1.0
    assert pytest.approx(matrix["BTC"]["GOLD"], 0.01) == -1.0
