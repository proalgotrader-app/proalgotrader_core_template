# ProAlgoTrader Core Template

Minimal template for algorithmic trading with FastAPI.

## Quick Start

```bash
# Install dependencies
uv sync

# Configure environment (see Environment Variables below)
# Run the application
uv run fastapi dev
```

## Project Structure

```
proalgotrader_core_template/
├── app/                    # FastAPI web UI
│   ├── core/              # Config and settings
│   ├── routers/           # API routes
│   ├── services/          # Business logic
│   ├── models/            # Database models
│   └── fasthtml_views/    # HTML views
├── db/                     # Database connection
├── static/                 # CSS, JS, images
├── proalgotrader_core/    # Trading engine
│   ├── algorithm.py       # Algorithm base class
│   ├── run_strategy.py    # Strategy runner
│   └── ...                # Other core modules
├── project/
│   └── strategy.py        # Your strategy implementation
├── run.py                  # Strategy subprocess entry
├── main.py                 # FastAPI entry point
└── pyproject.toml          # Dependencies
```

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

## Environment Variables

Create a `.env` file with the following **required** variables:

```env
# Required - Get from https://proalgotrader.com
PROJECT_KEY=your_project_key
PROJECT_SECRET=your_project_secret

# Required - OAuth credentials for authentication
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_client_secret
```

## Development

```bash
# Run in development mode
uv run fastapi dev

# Run strategy directly
uv run python run.py
```

## License

Private - All rights reserved.
