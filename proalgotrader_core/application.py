from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


class Application:
    def __init__(
        self,
        algorithm: AlgorithmProtocol,
    ) -> None:
        self.algorithm = algorithm

    async def start(self) -> None:
        await self.algorithm.logger.info("booting application", event="started")

        await self.algorithm.boot()

        await self.algorithm.logger.info("running application")

        await self.algorithm.run()

        await self.algorithm.logger.info(
            "application completed successfully", event="completed"
        )
