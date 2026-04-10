from proalgotrader_core.algorithm import Algorithm


class Strategy(Algorithm):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def initialize(self) -> None:
        pass

    async def next(self) -> None:
        pass
