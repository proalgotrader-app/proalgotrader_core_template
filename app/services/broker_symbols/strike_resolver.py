"""
Strike Resolver for calculating ATM-relative strike prices.

Provides functionality to:
- Calculate strike price relative to At-The-Money (ATM)
- Handle different strike sizes for different symbols
"""


def resolve_strike_price(ltp: float, strike_size: int, strike_price_input: int) -> int:
    """Convert ATM-relative strike input to actual strike price.

    This function calculates the strike price based on the current
    Last Traded Price (LTP) of the underlying and a relative offset
    from the At-The-Money (ATM) strike.

    Args:
        ltp: Current Last Traded Price of the underlying (e.g., 24167.50)
        strike_size: Strike increment from base_symbol (e.g., 50 for NIFTY)
        strike_price_input: ATM-relative offset:
            -2 = 2 strikes below ATM
            -1 = 1 strike below ATM
            0 = ATM (At The Money)
            1 = 1 strike above ATM
            2 = 2 strikes above ATM

    Returns:
        Actual strike price as integer (e.g., 24100, 24150, 24200)

    Examples:
        >>> # NIFTY at 24167.50, strike size 50
        >>> resolve_strike_price(24167.50, 50, 0)
        24150  # ATM rounded to nearest strike

        >>> resolve_strike_price(24167.50, 50, 1)
        24200  # One strike above ATM

        >>> resolve_strike_price(24167.50, 50, -1)
        24100  # One strike below ATM

        >>> # BANKNIFTY at 48032, strike size 100
        >>> resolve_strike_price(48032, 100, 0)
        48000

        >>> resolve_strike_price(48032, 100, 2)
        48200  # Two strikes above ATM

    Note:
        The ATM is calculated by rounding LTP to the nearest strike.
        For example, if NIFTY LTP is 24167.50 and strike size is 50:
        - ATM = round(24167.50 / 50) * 50 = round(483.35) * 50 = 483 * 50 = 24150
    """
    # Calculate ATM (At The Money) - round to nearest strike
    atm = round(ltp / strike_size) * strike_size

    # Apply offset
    strike_price = atm + (strike_size * strike_price_input)

    return int(strike_price)


def get_strike_prices_around_atm(
    ltp: float, strike_size: int, range_count: int = 5
) -> list[tuple[int, int]]:
    """Get strike prices around ATM with their offsets.

    Useful for displaying available strikes in UI.

    Args:
        ltp: Current Last Traded Price of the underlying
        strike_size: Strike increment from base_symbol
        range_count: Number of strikes on each side (default 5)

    Returns:
        List of tuples (strike_price, offset) sorted by strike_price

    Examples:
        >>> get_strike_prices_around_atm(24167.50, 50, 2)
        [(24050, -2), (24100, -1), (24150, 0), (24200, 1), (24250, 2)]
    """
    atm = round(ltp / strike_size) * strike_size

    strikes = []
    for i in range(-range_count, range_count + 1):
        strike = int(atm + (strike_size * i))
        strikes.append((strike, i))

    return strikes


def calculate_itm_otm(
    ltp: float, strike_price: int, option_type: str, strike_size: int
) -> str:
    """Determine if an option is ITM, OTM, or ATM.

    Args:
        ltp: Current Last Traded Price of the underlying
        strike_price: The option's strike price
        option_type: 'CE' for Call, 'PE' for Put
        strike_size: Strike increment (for ATM threshold)

    Returns:
        'ITM' (In-The-Money), 'OTM' (Out-The-Money), or 'ATM' (At-The-Money)

    Examples:
        >>> calculate_itm_otm(24150, 24000, 'CE', 50)
        'ITM'  # Call ITM when strike < spot

        >>> calculate_itm_otm(24150, 24000, 'PE', 50)
        'OTM'  # Put OTM when strike < spot

        >>> calculate_itm_otm(24150, 24150, 'CE', 50)
        'ATM'
    """
    atm = round(ltp / strike_size) * strike_size

    # ATM threshold (within 0.5% of strike size)
    atm_threshold = strike_size * 0.5

    if abs(strike_price - atm) <= atm_threshold:
        return "ATM"

    if option_type.upper() == "CE":
        # Call: ITM if strike < spot, OTM if strike > spot
        return "ITM" if strike_price < ltp else "OTM"
    else:  # PE
        # Put: ITM if strike > spot, OTM if strike < spot
        return "ITM" if strike_price > ltp else "OTM"


def get_suggested_strikes(
    ltp: float,
    strike_size: int,
    option_type: str,
    atm_count: int = 1,
    itm_count: int = 2,
    otm_count: int = 2,
) -> dict:
    """Get suggested strikes for trading.

    Returns strikes organized by ITM/ATM/OTM for given option type.

    Args:
        ltp: Current Last Traded Price of the underlying
        strike_size: Strike increment from base_symbol
        option_type: 'CE' for Call, 'PE' for Put
        atm_count: Number of ATM strikes (default 1)
        itm_count: Number of ITM strikes (default 2)
        otm_count: Number of OTM strikes (default 2)

    Returns:
        Dictionary with 'ATM', 'ITM', 'OTM' keys containing strike lists

    Examples:
        >>> get_suggested_strikes(24150, 50, 'CE', 1, 2, 2)
        {
            'ATM': [{'strike': 24150, 'offset': 0, 'premium_estimate': None}],
            'ITM': [
                {'strike': 24100, 'offset': -1},
                {'strike': 24050, 'offset': -2}
            ],
            'OTM': [
                {'strike': 24200, 'offset': 1},
                {'strike': 24250, 'offset': 2}
            ]
        }
    """
    atm = round(ltp / strike_size) * strike_size

    result = {"ATM": [], "ITM": [], "OTM": []}

    # ATM strikes
    for i in range(atm_count):
        strike = int(atm + (strike_size * i))
        result["ATM"].append(
            {
                "strike": strike,
                "offset": i,
            }
        )

    if option_type.upper() == "CE":
        # For Calls: ITM = lower strikes, OTM = higher strikes
        for i in range(1, itm_count + 1):
            strike = int(atm - (strike_size * i))
            result["ITM"].append(
                {
                    "strike": strike,
                    "offset": -i,
                }
            )

        for i in range(1, otm_count + 1):
            strike = int(atm + (strike_size * (atm_count + i - 1)))
            result["OTM"].append(
                {
                    "strike": strike,
                    "offset": atm_count + i - 1,
                }
            )
    else:  # PE
        # For Puts: ITM = higher strikes, OTM = lower strikes
        for i in range(1, itm_count + 1):
            strike = int(atm + (strike_size * i))
            result["ITM"].append(
                {
                    "strike": strike,
                    "offset": i,
                }
            )

        for i in range(1, otm_count + 1):
            strike = int(atm - (strike_size * i))
            result["OTM"].append(
                {
                    "strike": strike,
                    "offset": -i,
                }
            )

    return result
