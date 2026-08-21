from typing import Dict, List, Optional
import numpy as np


def compute_correlation_matrix(
    returns_dict: Dict[str, np.ndarray]
) -> Dict[str, Dict[str, float]]:
    """Compute pairwise Pearson correlation matrix for asset price returns arrays."""
    symbols = list(returns_dict.keys())
    if not symbols:
        return {}

    # Find minimum common length
    min_len = min(len(arr) for arr in returns_dict.values())
    if min_len < 2:
        # Return identity matrix if insufficient data points
        matrix: Dict[str, Dict[str, float]] = {}
        for s1 in symbols:
            matrix[s1] = {s2: 1.0 if s1 == s2 else 0.0 for s2 in symbols}
        return matrix

    # Truncate all arrays to min_len
    truncated_returns = {s: returns_dict[s][-min_len:] for s in symbols}

    matrix = {}
    for s1 in symbols:
        matrix[s1] = {}
        r1 = truncated_returns[s1]
        std1 = np.std(r1)
        for s2 in symbols:
            if s1 == s2:
                matrix[s1][s2] = 1.0
                continue
            r2 = truncated_returns[s2]
            std2 = np.std(r2)

            if std1 == 0 or std2 == 0:
                matrix[s1][s2] = 0.0
            else:
                corr = float(np.corrcoef(r1, r2)[0, 1])
                matrix[s1][s2] = round(corr, 4) if not np.isnan(corr) else 0.0

    return matrix
