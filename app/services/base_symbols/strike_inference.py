"""
Strike size inference from NSE option strikes.

Strike sizes are set by NSE and are universal across brokers.
Only representation differs (paisa vs rupees).
"""

# NSE-defined strike sizes for known symbols
NSE_STANDARD_STRIKE_SIZES = {
    "NIFTY": 50,
    "BANKNIFTY": 100,
    "FINNIFTY": 50,
    "MIDCPNIFTY": 25,
    "NIFTYNXT50": 100,
    "SENSEX": 100,  # BSE
    "BANKEX": 100,  # BSE
}


def infer_strike_size_from_strikes(normalized_strikes: list[int]) -> tuple[int, str]:
    """
    Infer strike_size from normalized strike prices.

    Since strike_size is set by NSE, ALL brokers will give same result
    after normalizing their representation (×1, ×100, etc.)

    Args:
        normalized_strikes: List of strike prices in RUPEES
                           (already divided by broker's multiplier)

    Returns:
        (strike_size, confidence)

    Example:
        >>> # Angel One: strikes = [2250000, 2255000, 2260000] (paisa)
        >>> multiplier = 100
        >>> normalized = [22500, 22550, 22600]
        >>> infer_strike_size_from_strikes(normalized)
        (50, 'High')

        >>> # Fyers: strikes = [22500, 22550, 22600] (rupees)
        >>> multiplier = 1
        >>> normalized = [22500, 22550, 22600]
        >>> infer_strike_size_from_strikes(normalized)
        (50, 'High')

        # BOTH GIVE SAME RESULT!

    Confidence Levels:
        - 'High': All strikes consistently spaced (≥90% min spacing)
        - 'Medium': Most strikes consistent (≥70% min spacing)
        - 'Low': Inconsistent spacing (<70%)
    """
    if len(normalized_strikes) < 2:
        return (0, "Low")

    # Sort strikes
    sorted_strikes = sorted(set(normalized_strikes))

    # Calculate differences between consecutive strikes
    differences = []
    for i in range(1, len(sorted_strikes)):
        diff = sorted_strikes[i] - sorted_strikes[i - 1]
        if diff > 0:  # Only positive differences
            differences.append(diff)

    if not differences:
        return (0, "Low")

    # Find minimum difference (NSE standard strike_size)
    min_diff = min(differences)

    # Validate: all differences should be divisible by min_diff
    # (Because NSE uses standard strike intervals)
    all_divisible = all(diff % min_diff == 0 for diff in differences)

    # Count how many strikes have minimum spacing
    # Near ATM: tight spacing (min_diff)
    # Far OTM/ITM: sometimes wider spacing
    min_count = sum(1 for diff in differences if diff == min_diff)
    ratio = min_count / len(differences)

    # Determine confidence
    if all_divisible and ratio >= 0.9:
        confidence = "High"  # Most strikes evenly spaced (normal)
    elif all_divisible and ratio >= 0.7:
        confidence = "Medium"  # Some wider gaps (still valid)
    elif all_divisible:
        confidence = "Low"  # Many wider gaps
    else:
        confidence = "Low"  # Inconsistent (shouldn't happen with NSE data)

    return (min_diff, confidence)


def validate_strike_size(
    symbol: str, inferred_strike_size: int, confidence: str
) -> tuple[bool, str]:
    """
    Validate inferred strike_size against known NSE standards.

    Args:
        symbol: Symbol name (NIFTY, BANKNIFTY, etc.)
        inferred_strike_size: Strike size inferred from catalog
        confidence: Confidence of inference

    Returns:
        (is_valid, message)

    Example:
        >>> validate_strike_size('NIFTY', 50, 'High')
        (True, 'Matches NSE standard')

        >>> validate_strike_size('NIFTY', 100, 'High')
        (False, 'Does not match NSE standard (50)')
    """
    if symbol not in NSE_STANDARD_STRIKE_SIZES:
        # No NSE standard defined for this symbol
        return (True, "No NSE standard defined, using inferred value")

    expected = NSE_STANDARD_STRIKE_SIZES[symbol]

    if inferred_strike_size == expected:
        return (True, "Matches NSE standard")
    else:
        return (
            False,
            f"Does not match NSE standard ({expected}). "
            f"Inferred: {inferred_strike_size}, confidence: {confidence}",
        )
