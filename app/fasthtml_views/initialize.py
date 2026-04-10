"""Project initialization page view using FastHTML.

Shows a loading screen or error if sync fails on server side.
"""

from fasthtml.common import (
    Body,
    Button,
    Div,
    Head,
    Html,
    Meta,
    Span,
    Style,
    Title,
    to_xml,
)


def initialize_page_html(error: str = None) -> str:
    """Generate the project initialization page HTML.

    Shows a loading screen while syncing project data.
    If error occurred, shows error with retry button.

    Args:
        error: Optional error message to display

    Returns:
        HTML string of the initialize page
    """
    # If there's an error, show error page with retry
    if error:
        page = Html(
            Head(
                Meta(charset="utf-8"),
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title("Initialization Failed - ProAlgoTrader"),
                Style(
                    """
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .container {
                        background: white;
                        padding: 3rem;
                        border-radius: 16px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        text-align: center;
                        max-width: 500px;
                        width: 90%;
                    }
                    .logo {
                        font-size: 2.5rem;
                        margin-bottom: 1rem;
                    }
                    h1 {
                        color: #333;
                        font-size: 1.75rem;
                        margin-bottom: 0.5rem;
                    }
                    .error {
                        color: #e74c3c;
                        background: #fce4e4;
                        padding: 1rem;
                        border-radius: 8px;
                        margin: 1rem 0;
                        font-size: 0.9rem;
                    }
                    .retry-btn {
                        background: #667eea;
                        color: white;
                        border: none;
                        padding: 0.75rem 2rem;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 1rem;
                        margin-top: 1rem;
                        text-decoration: none;
                        display: inline-block;
                    }
                    .retry-btn:hover {
                        background: #5568d3;
                    }
                    """
                ),
            ),
            Body(
                Div(
                    Span("⚠️", cls="logo"),
                    Div(
                        "Initialization Failed",
                        cls="",
                        style="font-size: 1.75rem; font-weight: bold; color: #333; margin-bottom: 0.5rem;",
                    ),
                    Div(error, cls="error"),
                    Button(
                        "Retry",
                        onclick="window.location.reload()",
                        style="background: #667eea; color: white; border: none; padding: 0.75rem 2rem; border-radius: 8px; cursor: pointer; font-size: 1rem; margin-top: 1rem;",
                    ),
                    cls="container",
                ),
                style="min-height: 100vh; margin: 0;",
            ),
        )
        return to_xml(page)

    # Show loading page (this will rarely be seen since sync happens on server)
    page = Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Initializing Project - ProAlgoTrader"),
            Style(
                """
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    background: white;
                    padding: 3rem;
                    border-radius: 16px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text-align: center;
                    max-width: 500px;
                    width: 90%;
                }
                .logo {
                    font-size: 2.5rem;
                    margin-bottom: 1rem;
                }
                h1 {
                    color: #333;
                    font-size: 1.75rem;
                    margin-bottom: 0.5rem;
                }
                .subtitle {
                    color: #666;
                    margin-bottom: 2rem;
                    font-size: 0.95rem;
                }
                .spinner {
                    width: 50px;
                    height: 50px;
                    margin: 2rem auto;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #667eea;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .status {
                    color: #888;
                    font-size: 0.9rem;
                    margin-top: 1rem;
                }
                """
            ),
        ),
        Body(
            Div(
                Span("🚀", cls="logo"),
                Div(
                    "Initializing Project",
                    cls="",
                    style="font-size: 1.75rem; font-weight: bold; color: #333; margin-bottom: 0.5rem;",
                ),
                Div(
                    "Setting up your project for the first time...",
                    cls="subtitle",
                ),
                Div(cls="spinner"),
                Div("Initializing...", cls="status"),
                cls="container",
            ),
            style="min-height: 100vh; margin: 0;",
        ),
    )

    return to_xml(page)
