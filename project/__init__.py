"""
Project Package for User Strategies.

This package is where users define their trading strategies.
It provides the base Strategy class that users can extend.

Example Usage:
    from project import Strategy

    class MyStrategy(Strategy):
        async def initialize(self):
            # Initialize your strategy
            await self.logger.info("Strategy initialized")

        async def next(self):
            # Execute trading logic
            await self.logger.info("Processing next candle")
"""

from project.strategy import Strategy

__all__ = ["Strategy"]
