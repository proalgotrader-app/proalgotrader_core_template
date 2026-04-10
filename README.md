# ProAlgoTrader Core Template

Minimal template for algorithmic trading with FastAPI.

## Quick Start

```bash
# Clone this repository
git clone https://github.com/proalgotrader-app/proalgotrader_core_template.git
cd proalgotrader_core_template

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your credentials

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

Create a `.env` file with the following:

```env
# Required
PROJECT_KEY=your_project_key
PROJECT_SECRET=your_project_secret
SECRET_KEY=your_secret_key

# Optional
REMOTE_API_URL=https://proalgotrader.com
LOCAL_API_URL=http://localhost:8000
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
