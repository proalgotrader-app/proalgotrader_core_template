import argparse
import os


def parse_arguments() -> argparse.Namespace:
    try:
        parser = argparse.ArgumentParser()

        parser.add_argument(
            "--local_api_url",
            default=os.getenv("LOCAL_API_URL", "http://localhost:8000"),
        )

        parser.add_argument(
            "--remote_api_url",
            default=os.getenv("REMOTE_API_URL", "https://proalgotrader.com"),
        )

        parser.add_argument("--api_token")

        parser.add_argument("--algo_session_id")

        return parser.parse_args()
    except Exception as e:
        print(e)
        raise Exception(e)


class ArgsManager:
    def __init__(self) -> None:
        self.arguments = parse_arguments()

        self.algo_session_id = self.arguments.algo_session_id
        self.local_api_url = self.arguments.local_api_url
        self.remote_api_url = self.arguments.remote_api_url
        self.api_token = self.arguments.api_token

    def validate_arguments(self) -> None:
        if not self.arguments.algo_session_id:
            raise Exception("ALGO SESSION ID is required")

        if not self.arguments.local_api_url:
            raise Exception("LOCAL API URL is required")

        if not self.arguments.remote_api_url:
            raise Exception("REMOTE API URL is required")

        if not self.arguments.api_token:
            raise Exception("API TOKEN is required")
