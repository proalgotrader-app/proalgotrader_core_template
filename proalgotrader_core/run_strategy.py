import asyncio

from dotenv import load_dotenv

from proalgotrader_core.api import Api
from proalgotrader_core.application import Application
from proalgotrader_core.args_manager import ArgsManager
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol

# Setup the loop at module level
try:
    event_loop = asyncio.get_running_loop()
except RuntimeError:
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)


async def start_with_factory(strategy_class: type[AlgorithmProtocol]) -> None:
    """
    Start function that uses the factory pattern to create
    Algorithm with pre-initialized AlgoSession
    """
    load_dotenv(verbose=True, override=True)

    args_manager = ArgsManager()

    args_manager.validate_arguments()

    api = Api(args_manager=args_manager)

    algo_session_info = await api.get_algo_session_info()

    algorithm = strategy_class(
        event_loop=event_loop,
        args_manager=args_manager,
        api=api,
        algo_session_info=algo_session_info,
    )

    # Connect WebSocket
    await algorithm.logger.connect()

    # Create application with the pre-initialized algorithm and logger
    application = Application(algorithm=algorithm)

    try:
        # Notify that strategy started
        await algorithm.logger.info("Strategy started", event="started")

        await application.start()
    except Exception as e:
        # Log error
        await algorithm.logger.error(
            f"Application failed: {str(e)}", event="error", data={"error": str(e)}
        )
        raise
    finally:
        # Give time for final messages to be sent before closing
        await asyncio.sleep(1)
        await algorithm.logger.close()


def run_strategy(strategy_class: type[AlgorithmProtocol]) -> None:
    """
    Start function that uses the factory pattern for better initialization
    """
    try:
        event_loop.run_until_complete(start_with_factory(strategy_class=strategy_class))
    except:
        raise
    finally:
        event_loop.close()
