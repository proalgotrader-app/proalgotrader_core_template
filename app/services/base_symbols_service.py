"""
Base symbols service for ProAlgoTrader FastAPI.

Handles syncing base symbols from broker catalog to database.
"""

from sqlmodel import Session

from app.services.base_symbols.base_symbol_extractor import BaseSymbolExtractor
from db.database import global_engine


async def sync_base_symbols_from_catalog(broker: str = "angel-one") -> dict:
    """
    Sync base symbols from broker catalog to database.

    Args:
        broker: Broker catalog to use (default: angel-one)

    Returns:
        Dict with sync results:
        {
            "success": bool,
            "broker": str,
            "total": int,
            "added": int,
            "updated": int,
            "unchanged": int
        }
    """
    try:
        db = Session(global_engine)
        extractor = BaseSymbolExtractor(db, broker)
        catalog_symbols = extractor.extract_nse_fno_symbols()
        stats = extractor.store_symbols(catalog_symbols)
        db.close()

        return {
            "success": True,
            "broker": broker,
            "total": len(catalog_symbols),
            "added": stats["added"],
            "updated": stats["updated"],
            "unchanged": stats["unchanged"],
        }
    except Exception as e:
        print(f"[Base Symbols Service] Error syncing: {e}")
        return {"success": False, "error": str(e)}
