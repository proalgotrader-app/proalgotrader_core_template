"""
Angel One broker adapter for extracting base symbols from catalog.

Angel One specifics:
- Strike prices stored as paisa (×100 multiplier)
- Expiry format: DDMMMYYYY (26DEC2024)
- Column names: name, strike, lotsize, expiry
- Exchange codes: NSE (cash), NFO (derivatives)
"""

from app.services.base_symbols.adapters.base_adapter import BaseSymbolAdapter


class AngelOneBaseSymbolAdapter(BaseSymbolAdapter):
    """
    Extract base symbols from Angel One catalog.

    Angel One Catalog Details:
    - Strike prices: Stored as paisa (×100)
      Example: 22500.00 rupees → 2250000.000000 in catalog
    - Column names: name, strike, lotsize, expiry, token
    - Expiry format: DDMMMYYYY (26DEC2024)
    - Exchanges: NSE (cash), NFO (derivatives)
    """

    def get_column_mappings(self) -> dict[str, str]:
        """
        Get Angel One column mappings.

        Angel One uses:
        - 'name' for base symbol name
        - 'strike' for strike price (in paisa)
        - 'lotsize' for lot size
        - 'expiry' for expiry date
        """
        return {
            "symbol": "name",  # Base symbol name
            "strike": "strike",  # Strike price (paisa)
            "lotsize": "lotsize",  # Lot size
            "expiry": "expiry",  # Expiry date
            "token": "token",  # Instrument token
        }

    def get_strike_multiplier(self) -> int:
        """
        Angel One stores strikes in paisa (×100).

        Returns:
            100 (divide by 100 to get rupees)

        Example:
            Angel One catalog: 2250000.000000
            After division: 22500 (rupees)
        """
        return 100

    def get_exchange_filter(self) -> dict[str, str]:
        """
        Get Angel One exchange filter for NSE F&O.

        Angel One uses:
        - 'NFO' for NSE derivatives
        - 'NSE' for NSE cash market

        Returns:
            {'exchange': 'NFO'} for NSE F&O symbols
        """
        return {"exchange": "NFO"}
