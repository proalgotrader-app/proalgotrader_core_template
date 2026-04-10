"""Login page view using FastHTML.

This replicates the original login_oauth.html template using FastHTML components.
"""


def login_page_html(error: str = None) -> str:
    """Generate the login page HTML matching the original template.

    Args:
        error: Optional error message to display

    Returns:
        HTML string of the login page
    """
    from fasthtml.common import (
        Body,
        Button,
        Div,
        Head,
        Html,
        Meta,
        Script,
        Span,
        Style,
        Title,
        to_xml,
    )

    # Error display style
    error_display = "block" if error else "none"
    error_message = error or ""

    page = Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Authorize - ProAlgoTrader"),
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
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                    margin: 0;
                }
                .container {
                    background: white;
                    border-radius: 20px;
                    padding: 50px 40px;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    max-width: 450px;
                    width: 100%;
                    text-align: center;
                }
                .logo {
                    font-size: 48px;
                    margin-bottom: 20px;
                }
                h1 {
                    color: #333;
                    font-size: 28px;
                    margin-bottom: 10px;
                    font-weight: 700;
                }
                .subtitle {
                    color: #666;
                    font-size: 16px;
                    margin-bottom: 40px;
                    line-height: 1.5;
                }
                .error-message {
                    background: #fee;
                    color: #c00;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 25px;
                    font-size: 14px;
                    border: 1px solid #fcc;
                    display: """
                + error_display
                + """;
                }
                .btn-authorize {
                    width: 100%;
                    padding: 15px 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s ease, box-shadow 0.2s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 10px;
                    margin-bottom: 25px;
                }
                .btn-authorize:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                }
                .btn-authorize:active {
                    transform: translateY(0);
                }
                .btn-authorize:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                    transform: none;
                }
                .authorize-icon {
                    font-size: 20px;
                }
                .loading {
                    display: inline-block;
                    width: 16px;
                    height: 16px;
                    border: 2px solid #fff;
                    border-radius: 50%;
                    border-top-color: transparent;
                    animation: spin 0.8s linear infinite;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                .features {
                    text-align: left;
                    margin-top: 30px;
                    padding-top: 30px;
                    border-top: 1px solid #eee;
                }
                .feature {
                    display: flex;
                    align-items: center;
                    margin-bottom: 12px;
                    color: #666;
                    font-size: 14px;
                }
                .feature-icon {
                    margin-right: 10px;
                    font-size: 18px;
                }
                .helper-text {
                    text-align: left;
                    margin-top: 25px;
                    color: #666;
                    font-size: 13px;
                }
                .helper-text a {
                    color: #667eea;
                    text-decoration: none;
                    font-weight: 600;
                }
                .helper-text a:hover {
                    text-decoration: underline;
                }
            """
            ),
        ),
        Body(
            Div(
                Div("🚀", cls="logo"),
                Div(
                    "Welcome to ProAlgoTrader",
                    **{"class": "h1"},
                    style="color: #333; font-size: 28px; margin-bottom: 10px; font-weight: 700;",
                ),
                Div(
                    "Connect your ProAlgoTrader account to manage your trading strategies",
                    cls="subtitle",
                ),
                Div(
                    error_message,
                    id="error-message",
                    cls="error-message",
                ),
                Button(
                    Span("🔐", cls="authorize-icon"),
                    Span("Authorize with ProAlgoTrader", id="btn-text"),
                    cls="btn-authorize",
                    id="authorize-btn",
                    onclick="authorize()",
                ),
                Div(
                    Div(
                        Span("✅", cls="feature-icon"),
                        Span("Secure OAuth2 authentication"),
                        cls="feature",
                    ),
                    Div(
                        Span("✅", cls="feature-icon"),
                        Span("No API keys stored locally"),
                        cls="feature",
                    ),
                    Div(
                        Span("✅", cls="feature-icon"),
                        Span("Manage multiple projects"),
                        cls="feature",
                    ),
                    Div(
                        Span("✅", cls="feature-icon"),
                        Span("Automatic token refresh"),
                        cls="feature",
                    ),
                    cls="features",
                ),
                Div(
                    "Don't have an account? ",
                    Span(
                        "Sign up here",
                        style="color: #667eea; text-decoration: none; font-weight: 600; cursor: pointer;",
                        onclick="window.open('https://proalgotrader.com', '_blank')",
                    ),
                    cls="helper-text",
                ),
                cls="container",
            ),
            Script(_login_script(error_message)),
        ),
    )

    return to_xml(page)


def _login_script(error: str) -> str:
    """Return the login page JavaScript."""
    return """
        // Store redirect destination for OAuth callback
        const postLoginRedirect = '/dashboard';

        // Check for error in URL params
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');

        if (error) {
            showError(decodeURIComponent(error));
        }

        function showError(message) {
            const errorDiv = document.getElementById('error-message');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        async function authorize() {
            console.log('[OAuth] Starting authorization flow');

            const btn = document.getElementById('authorize-btn');
            const btnText = document.getElementById('btn-text');

            // Disable button and show loading
            btn.disabled = true;
            btnText.innerHTML = '<span class="loading"></span> Redirecting...';

            try {
                // Get OAuth configuration from server
                const response = await fetch('/api/oauth/config');
                if (!response.ok) {
                    throw new Error('Failed to get OAuth configuration');
                }
                const config = await response.json();

                console.log('[OAuth] Config:', config);

                // Build authorization URL with state parameter for CSRF protection
                const authUrl = config.auth_url;
                const params = new URLSearchParams({
                    client_id: config.client_id,
                    redirect_uri: config.redirect_uri,
                    response_type: 'code',
                    state: config.state  // Include state for CSRF protection
                });

                // Store redirect destination in cookie for OAuth callback
                document.cookie = 'oauth_redirect_to=' + postLoginRedirect + '; path=/; max-age=600';

                const fullUrl = `${authUrl}?${params.toString()}`;
                console.log('[OAuth] Redirecting to:', fullUrl);
                console.log('[OAuth] State:', config.state);
                console.log('[OAuth] Post-login redirect:', postLoginRedirect);

                // Redirect to ProAlgoTrader OAuth
                window.location.href = fullUrl;
            } catch (error) {
                console.error('[OAuth] Error:', error);
                showError('Failed to start authorization. Please try again.');
                btn.disabled = false;
                btnText.textContent = 'Authorize with ProAlgoTrader';
            }
        }

        // Auto-trigger if coming from logout
        const autoAuth = urlParams.get('auto');
        if (autoAuth === 'true') {
            console.log('[OAuth] Auto-authorizing');
            setTimeout(() => authorize(), 500);
        }
    """
