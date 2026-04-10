"""Dashboard view using FastHTML.

This replicates the original dashboard.html template using FastHTML components.
The UI structure and styling is preserved from the original template.
"""

from fasthtml.common import *  # noqa: F403, F405

from .components import confirmation_modal, get_modal_styles


def dashboard_page_html(user_name: str = None) -> str:
    """Generate the complete dashboard HTML matching the original template.

    This function generates HTML that is identical to templates/dashboard.html
    but using FastHTML components for better maintainability.

    Args:
        user_name: Optional user name to display in navbar

    Returns:
        HTML string of the complete dashboard page
    """

    page = Html(
        Head(
            Meta(charset="utf-8"),
            Meta(
                name="viewport",
                content="width=device-width, initial-scale=1.0",
            ),
            Title("Dashboard - ProAlgoTrader"),
            Link(rel="stylesheet", href="/static/css/shared.css?v=3"),
            Style(_dashboard_styles()),
        ),
        Body(
            # Old navbar container (for OLD routes)
            # FastHTML navbar container (for FASTHTML routes)
            Div(id="navbar-container"),
            # Success toast (for project sync)
            Div(
                "Project info synced successfully!",
                id="success-toast",
                cls="success-toast",
            ),
            # Generic toast (for other operations like token generation)
            Div("", id="toast", cls="toast"),
            # Token Regeneration Confirmation Modal
            confirmation_modal(
                modal_id="regenerate-modal",
                title="Regenerate Token?",
                message="This will generate a new broker token. Your current token will stop working immediately.\n\nThis action cannot be undone.",
                submit_text="Regenerate",
                submit_onclick="confirmRegenerate()",
                cancel_onclick="closeRegenerateModal()",
            ),
            # Generate Token Confirmation Modal
            confirmation_modal(
                modal_id="generate-modal",
                title="Generate Token?",
                message="This will generate a new broker token for trading.\n\nTokens are valid until 9:00 AM IST the next day.",
                submit_text="Generate",
                submit_onclick="confirmGenerate()",
                cancel_onclick="closeGenerateModal()",
            ),
            # Sync Project Confirmation Modal
            confirmation_modal(
                modal_id="sync-modal",
                title="Sync Project?",
                message="This will fetch the latest project data from the server.\n\nNote: Sync is not allowed while an algo session is running.",
                submit_text="Sync",
                submit_onclick="confirmSync()",
                cancel_onclick="closeSyncModal()",
            ),
            # Main content
            Div(
                # Page header
                Div(
                    H1("📊 Dashboard", cls="page-title"),
                    Div(
                        Span("", id="last-synced", cls="last-synced"),
                        Button(
                            svg_sync_icon(cls="sync-icon", id="sync-icon"),
                            Span("Sync", id="sync-text"),
                            id="sync-btn",
                            cls="btn-sync",
                            onclick="showSyncModal()",
                        ),
                        cls="header-actions",
                    ),
                    cls="page-header",
                ),
                # Tabs container
                Div(
                    # Tab buttons
                    Div(
                        Button(
                            "Overview",
                            cls="tab-btn active",
                            data_tab="overview",
                            onclick="switchTab('overview')",
                        ),
                        Button(
                            "Broker",
                            cls="tab-btn",
                            data_tab="broker",
                            onclick="switchTab('broker')",
                        ),
                        Button(
                            "Strategy",
                            cls="tab-btn",
                            data_tab="strategy",
                            onclick="switchTab('strategy')",
                        ),
                        cls="tabs-header",
                    ),
                    # Tab content containers
                    # Overview Tab
                    Div(
                        Div(
                            Div(
                                Div(cls="spinner"),
                                P("Loading..."),
                                cls="loading",
                            ),
                            id="overview-content",
                        ),
                        id="tab-overview",
                        cls="tab-content active",
                    ),
                    # Broker Tab
                    Div(
                        Div(
                            Div(
                                Div(cls="spinner"),
                                P("Loading..."),
                                cls="loading",
                            ),
                            id="broker-content",
                        ),
                        id="tab-broker",
                        cls="tab-content",
                    ),
                    # Strategy Tab
                    Div(
                        Div(
                            Div(
                                Div(cls="spinner"),
                                P("Loading..."),
                                cls="loading",
                            ),
                            id="strategy-content",
                        ),
                        id="tab-strategy",
                        cls="tab-content",
                    ),
                    cls="tabs-container",
                ),
                cls="main-content",
            ),
            # Scripts
            Script(src="/static/js/user-state.js"),
            Script(src="/static/js/navbar.js?v=16"),
            Script(_dashboard_script()),
        ),
    )

    return to_xml(page)


def svg_sync_icon(**kwargs):
    """SVG sync icon using NotStr for proper rendering."""
    from fasthtml.common import NotStr

    # Build icon class
    icon_cls = "sync-icon"
    if "cls" in kwargs:
        icon_cls = kwargs.pop("cls")

    # Build SVG with proper paths (circular refresh arrows)
    svg_content = f"""<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="{icon_cls}">
  <path d="M23 4v6h-6"/>
  <path d="M1 20v-6h6"/>
  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"/>
  <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"/>
</svg>"""

    # Add any additional attributes
    for key, value in kwargs.items():
        svg_content = svg_content.replace("<svg", f'<svg {key}="{value}"', 1)

    return NotStr(svg_content)


def _dashboard_styles() -> str:
    """Return the dashboard CSS styles matching the original template."""
    return (
        get_modal_styles()
        + """

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 0;
        }

        .main-content {
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }

        .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            background: white;
            padding: 20px 30px;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .page-title {
            font-size: 28px;
            font-weight: 700;
            color: #333;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .last-synced {
            font-size: 13px;
            color: #666;
        }

        .btn-sync {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-sync:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-sync:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-sync.syncing {
            background: #6c757d;
        }

        .sync-icon {
            width: 18px;
            height: 18px;
            display: inline-block;
            vertical-align: middle;
        }

        .sync-icon.spinning {
            animation: spin 1s linear infinite;
        }

        .btn-sync:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        /* Tabs */
        .tabs-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }

        .tabs-header {
            display: flex;
            border-bottom: 1px solid #e0e0e0;
            overflow-x: auto;
        }

        .tab-btn {
            padding: 15px 25px;
            background: none;
            border: none;
            font-size: 14px;
            font-weight: 600;
            color: #666;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            white-space: nowrap;
        }

        .tab-btn:hover {
            color: #667eea;
            background: #f8f9fa;
        }

        .tab-btn.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }

        .tab-content {
            display: none;
            padding: 30px;
        }

        .tab-content.active {
            display: block;
        }

        /* Cards */
        .card {
            background: white;
            padding: 0;
        }

        .section {
            margin-bottom: 30px;
        }

        .section h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }

        .section h3 {
            color: #333;
            font-size: 16px;
            margin-bottom: 15px;
            margin-top: 20px;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .info-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }

        .info-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }

        .info-value {
            font-size: 16px;
            color: #333;
            font-weight: 600;
            word-break: break-all;
        }

        .status-active {
            color: #27ae60;
            font-weight: 600;
        }

        .status-inactive {
            color: #e74c3c;
            font-weight: 600;
        }

        /* Config section */
        .config-section {
            margin-top: 20px;
        }

        .config-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }

        .config-item {
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #764ba2;
        }

        .config-key {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
            margin-bottom: 3px;
        }

        .config-value {
            font-family: monospace;
            font-size: 14px;
            color: #333;
            word-break: break-all;
        }

        .mask-value {
            color: #999;
        }

        /* Token section */
        .token-status {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }

        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-badge.active {
            background: #d4edda;
            color: #155724;
        }

        .status-badge.inactive {
            background: #f8d7da;
            color: #721c24;
        }

        .btn-generate {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn-generate:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-generate:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-generate.secondary {
            background: #6c757d;
        }

        .token-value {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 13px;
            word-break: break-all;
            margin-top: 10px;
            border-left: 4px solid #667eea;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
        }

        .token-text {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .copy-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: background 0.2s;
            flex-shrink: 0;
        }

        .copy-btn:hover {
            background: #5a67d8;
        }

        .copy-btn.copied {
            background: #27ae60;
        }

        .copy-icon {
            width: 16px;
            height: 16px;
        }

        .token-info {
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }

        /* Modal styles */

        /* Plan section */
        .plan-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
        }

        .plan-name {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .plan-features {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .plan-feature {
            display: flex;
            align-items: center;
            gap: 5px;
            font-size: 14px;
        }

        .plan-feature.enabled {
            color: #d4edda;
        }

        .plan-feature.disabled {
            color: #f8d7da;
        }

        /* GitHub section */
        .github-repo {
            background: #24292e;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }

        .github-repo h3 {
            color: white;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .github-repo a {
            color: #58a6ff;
            text-decoration: none;
        }

        .github-repo a:hover {
            text-decoration: underline;
        }

        /* Loading */
        .loading {
            text-align: center;
            padding: 40px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .success-toast {
            position: fixed;
            top: 80px;
            right: 20px;
            min-width: 280px;
            max-width: 350px;
            background: #27ae60;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 1000;
            display: none;
            font-weight: 600;
            word-wrap: break-word;
        }

        .success-toast.show {
            display: block;
            animation: slideInToast 0.3s ease;
        }

        .toast {
            position: fixed;
            top: 80px;
            right: 20px;
            min-width: 280px;
            max-width: 350px;
            padding: 15px 25px;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            opacity: 0;
            transform: translateX(100%);
            transition: opacity 0.3s, transform 0.3s;
            z-index: 1001;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            word-wrap: break-word;
        }

        .toast.show {
            opacity: 1;
            transform: translateX(0);
        }

        .toast.success {
            background: #27ae60;
        }

        .toast.error {
            background: #e74c3c;
        }

        @keyframes slideInToast {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    """
    )


def _dashboard_script() -> str:
    """Return the dashboard JavaScript matching the original template exactly."""
    # This JavaScript is identical to templates/dashboard.html
    # Only changing initNavbar() to initNavbar() for dual navbar support
    return """
        // Global state
        let projectData = null;

        // Tab switching with URL support
        function switchTab(tabName) {
            // Update URL query parameter
            const url = new URL(window.location);
            url.searchParams.set('tab', tabName);
            window.history.replaceState({}, '', url);

            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tab === tabName);
            });

            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.toggle('active', content.id === `tab-${tabName}`);
            });
        }

        // Get initial tab from URL
        function getInitialTab() {
            const params = new URLSearchParams(window.location.search);
            const tab = params.get('tab');
            // Validate tab is one of the valid tabs
            const validTabs = ['overview', 'broker', 'strategy'];
            return validTabs.includes(tab) ? tab : 'overview';
        }

        // Load project data
        async function loadProjectData() {
            try {
                const response = await fetch('/api/project/info');
                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(data.detail || 'Failed to fetch project info');
                }

                projectData = data;
                renderAllTabs(data);

                // Update last synced
                document.getElementById('last-synced').textContent =
                    `Last synced: ${new Date().toLocaleString()}`;

            } catch (error) {
                console.error('Error loading project data:', error);
                showError(error.message);
            }
        }

        // Render all tabs
        function renderAllTabs(data) {
            renderOverviewTab(data);
            renderBrokerTab(data);
            renderStrategyTab(data);
        }

        // Overview Tab
        function renderOverviewTab(data) {
            const project = data.project || {};
            const container = document.getElementById('overview-content');

            container.innerHTML = `
                <div class="section">
                    <h2>Project Details</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Project ID</div>
                            <div class="info-value">${project.id || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Project Name</div>
                            <div class="info-value">${project.name || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Project Key</div>
                            <div class="info-value">${project.key || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Status</div>
                            <div class="info-value ${project.status === 'active' ? 'status-active' : 'status-inactive'}">
                                ${project.status || 'N/A'}
                            </div>
                        </div>
                        ${project.created_at ? `
                        <div class="info-item">
                            <div class="info-label">Created At</div>
                            <div class="info-value">${new Date(project.created_at).toLocaleString()}</div>
                        </div>
                        ` : ''}
                        ${project.updated_at ? `
                        <div class="info-item">
                            <div class="info-label">Updated At</div>
                            <div class="info-value">${new Date(project.updated_at).toLocaleString()}</div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        // Broker Tab
        function renderBrokerTab(data) {
            const broker = data.project?.broker || {};
            const container = document.getElementById('broker-content');

            if (!broker.id) {
                container.innerHTML = `
                    <div class="section">
                        <h2>Broker</h2>
                        <p>No broker configured for this project.</p>
                    </div>
                `;
                return;
            }

            const brokerConfig = broker.broker_config || {};

            container.innerHTML = `
                <div class="section">
                    <h2>Broker Information</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Broker Name</div>
                            <div class="info-value">${broker.broker_name || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Broker Title</div>
                            <div class="info-value">${broker.broker_title || 'N/A'}</div>
                        </div>
                    </div>
                </div>

                ${Object.keys(brokerConfig).length > 0 ? `
                <div class="section">
                    <h2>Broker Configuration</h2>
                    <div class="config-grid">
                        ${Object.entries(brokerConfig).map(([key, value]) => `
                        <div class="config-item">
                            <div class="config-key">${formatKey(key)}</div>
                            <div class="config-value ${shouldMask(key) ? 'mask-value' : ''}">${shouldMask(key) ? maskValue(value) : (value || 'N/A')}</div>
                        </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}

                <div class="section">
                    <h2>Broker Token</h2>
                    <div id="token-content">
                        <div class="token-status">
                            <span class="status-badge">Loading...</span>
                        </div>
                    </div>
                </div>
            `;

            // Load token after rendering broker info
            loadBrokerToken();
        }

        // Load broker token
        async function loadBrokerToken() {
            try {
                const broker = projectData?.project?.broker || {};
                const brokerId = broker.id;
                const brokerTitle = broker.broker_title || 'angel-one';

                const response = await fetch(`/api/brokers/${brokerTitle}/token?broker_id=${brokerId}`);

                if (response.ok) {
                    const data = await response.json();
                    renderToken(data.token, data.feed_token, true);
                } else if (response.status === 404) {
                    renderToken(null, null, false);
                } else {
                    const error = await response.json();
                    console.error('Token error:', error);
                    renderToken(null, null, false);
                }
            } catch (error) {
                console.error('Error loading token:', error);
                renderToken(null, null, false);
            }
        }

        // Mask a token showing only first and last N characters
        function maskToken(token, showChars = 8) {
            if (!token) return '';
            if (token.length <= showChars * 2) {
                return token.substring(0, 4) + '****';
            }
            const start = token.substring(0, showChars);
            const end = token.substring(token.length - showChars);
            return `${start}****${end}`;
        }

        // Copy token to clipboard
        async function copyToken(token, btn) {
            try {
                await navigator.clipboard.writeText(token);
                btn.classList.add('copied');
                btn.innerHTML = `
                    <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Copied!
                `;
                setTimeout(() => {
                    btn.classList.remove('copied');
                    btn.innerHTML = `
                        <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        Copy
                    `;
                }, 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        }

        // Render token section
        function renderToken(token, feedToken, reused) {
            const content = document.getElementById('token-content');

            if (token) {
                content.innerHTML = `
                    <div class="token-status">
                        <span class="status-badge active">Active</span>
                        ${reused ? '<span style="color: #667eea; font-size: 12px;">Reused existing token</span>' : '<span style="color: #27ae60; font-size: 12px;">New token generated</span>'}
                    </div>
                    <div class="info-grid" style="margin-top: 15px;">
                        <div class="info-item">
                            <div class="info-label">JWT Token</div>
                            <div class="token-value">
                                <span class="token-text" title="${token}">${maskToken(token)}</span>
                                <button class="copy-btn" onclick="copyToken('${token}', this)">
                                    <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                                    </svg>
                                    Copy
                                </button>
                            </div>
                        </div>
                        ${feedToken ? `
                        <div class="info-item">
                            <div class="info-label">Feed Token</div>
                            <div class="token-value">
                                <span class="token-text" title="${feedToken}">${maskToken(feedToken)}</span>
                                <button class="copy-btn" onclick="copyToken('${feedToken}', this)">
                                    <svg class="copy-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                                    </svg>
                                    Copy
                                </button>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="token-info">
                        Tokens are valid until 9:00 AM IST the next day.
                    </div>
                    <button class="btn-generate secondary" onclick="regenerateToken()">
                        <svg class="sync-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 4v6h-6"></path>
                            <path d="M1 20v-6h6"></path>
                            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"></path>
                            <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"></path>
                        </svg>
                        Regenerate Token
                    </button>
                `;
            } else {
                content.innerHTML = `
                    <div class="token-status">
                        <span class="status-badge inactive">No Token</span>
                    </div>
                    <p style="color: #666; margin: 15px 0;">
                        No broker token found. Generate one to start trading.
                    </p>
                    <button class="btn-generate" onclick="showGenerateModal()">
                        <svg class="sync-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 4v6h-6"></path>
                            <path d="M1 20v-6h6"></path>
                            <path d="M3.51 9a9 0 0 1 14.85-3.36L23 10"></path>
                            <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"></path>
                        </svg>
                        Generate Token
                    </button>
                `;
            }
        }

        // Generate token (get or create)
        function showGenerateModal() {
            document.getElementById('generate-modal').classList.add('active');
        }

        function closeGenerateModal() {
            document.getElementById('generate-modal').classList.remove('active');
        }

        async function confirmGenerate() {
            closeGenerateModal();
            await generateToken();
        }

        async function generateToken() {
            const btn = document.querySelector('.btn-generate');
            const originalHTML = btn.innerHTML;

            try {
                btn.disabled = true;
                btn.innerHTML = '<svg class="sync-icon spinning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path><path d="M3.51 9a9 0 0 1 14.85-3.36L23 10"></path><path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"></path></svg> Generating...';

                const broker = projectData?.project?.broker || {};
                const brokerId = broker.id;
                const brokerTitle = broker.broker_title || 'angel-one';
                const brokerConfig = broker.broker_config || {};

                const payload = {
                    broker_id: brokerId,
                    ...brokerConfig
                };

                // POST to /generate endpoint
                const response = await fetch(`/api/brokers/${brokerTitle}/generate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to generate token');
                }

                const data = await response.json();

                if (data.success) {
                    showToast(data.message || 'Token generated successfully!', 'success');
                    renderToken(data.token, data.feed_token, !data.generated);
                } else {
                    throw new Error('Token generation failed');
                }

            } catch (error) {
                console.error('Error generating token:', error);
                showToast(error.message || 'Failed to generate token', 'error');
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }
        }

        // Regenerate token (always creates new)
        async function regenerateToken() {
            // Show confirmation modal
            showRegenerateModal();
        }

        // Show regenerate confirmation modal
        function showRegenerateModal() {
            document.getElementById('regenerate-modal').classList.add('active');
        }

        // Close regenerate modal
        function closeRegenerateModal() {
            document.getElementById('regenerate-modal').classList.remove('active');
        }

        // Confirm regenerate token
        async function confirmRegenerate() {
            closeRegenerateModal();

            const btn = document.querySelector('.btn-generate.secondary');
            const originalHTML = btn ? btn.innerHTML : '<svg class="sync-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path><path d="M3.51 9a9 0 0 1 14.85-3.36L23 10"></path><path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"></path></svg> Regenerate Token';

            try {
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<svg class="sync-icon spinning" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"></path><path d="M1 20v-6h6"></path><path d="M3.51 9a9 0 0 1 14.85-3.36L23 10"></path><path d="M20.49 15a9 0 0 1-14.85 3.36L1 14"></path></svg> Regenerating...';
                }

                const broker = projectData?.project?.broker || {};
                const brokerId = broker.id;
                const brokerTitle = broker.broker_title || 'angel-one';
                const brokerConfig = broker.broker_config || {};

                const payload = {
                    broker_id: brokerId,
                    ...brokerConfig
                };

                const response = await fetch(`/api/brokers/${brokerTitle}/regenerate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to regenerate token');
                }

                const data = await response.json();

                if (data.success) {
                    showToast(data.message || 'Token regenerated successfully!', 'success');
                    renderToken(data.token, data.feed_token, false);
                } else {
                    throw new Error('Token regeneration failed');
                }

            } catch (error) {
                console.error('Error regenerating token:', error);
                showToast(error.message || 'Failed to regenerate token', 'error');
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = originalHTML;
                }
            }
        }

        // Strategy Tab
        function renderStrategyTab(data) {
            const strategy = data.project?.strategy || {};
            const container = document.getElementById('strategy-content');

            if (!strategy.id) {
                container.innerHTML = `
                    <div class="section">
                        <h2>Strategy</h2>
                        <p>No strategy configured for this project.</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="section">
                    <h2>Strategy Information</h2>
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Strategy ID</div>
                            <div class="info-value">${strategy.id || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Identifier</div>
                            <div class="info-value">${strategy.identifier || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Title</div>
                            <div class="info-value">${strategy.title || 'N/A'}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Description</div>
                            <div class="info-value">${strategy.description || 'No description'}</div>
                        </div>
                    </div>
                </div>

                ${strategy.github_repository ? `
                <div class="section">
                    <div class="github-repo">
                        <h3 style="color: white; margin-bottom: 15px;">📦 GitHub Repository</h3>
                        <div class="info-grid" style="margin-top: 15px;">
                            <div class="info-item" style="background: rgba(255,255,255,0.1); border-left-color: #58a6ff;">
                                <div class="info-label" style="color: #ccc;">Repository</div>
                                <div class="info-value" style="color: #58a6ff;">
                                    <a href="https://github.com/${strategy.github_repository.repository_full_name}" target="_blank" style="color: #58a6ff;">
                                        ${strategy.github_repository.repository_full_name || 'N/A'}
                                    </a>
                                </div>
                            </div>
                            <div class="info-item" style="background: rgba(255,255,255,0.1); border-left-color: #58a6ff;">
                                <div class="info-label" style="color: #ccc;">Owner</div>
                                <div class="info-value" style="color: white;">${strategy.github_repository.repository_owner || 'N/A'}</div>
                            </div>
                        </div>
                    </div>
                </div>
                ` : ''}
            `;
        }

        // Helper functions
        function formatKey(key) {
            return key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').trim();
        }

        function shouldMask(key) {
            const sensitiveKeys = ['secret', 'password', 'token', 'api_key', 'api_secret', 'access_token', 'pin', 'totp'];
            return sensitiveKeys.some(s => key.toLowerCase().includes(s));
        }

        function maskValue(value) {
            if (!value || typeof value !== 'string') return '••••••••';
            if (value.length <= 16) return '••••••••';
            return value.substring(0, 4) + '****' + value.substring(value.length - 4);
        }

        // Sync project
        // Show sync confirmation modal
        function showSyncModal() {
            document.getElementById('sync-modal').classList.add('active');
        }

        // Close sync modal
        function closeSyncModal() {
            document.getElementById('sync-modal').classList.remove('active');
        }

        // Confirm and execute sync
        async function confirmSync() {
            closeSyncModal();
            await syncProject();
        }

        async function syncProject() {
            const syncBtn = document.getElementById('sync-btn');
            const icon = document.getElementById('sync-icon');
            const text = document.getElementById('sync-text');
            const successToast = document.getElementById('success-toast');

            syncBtn.disabled = true;
            syncBtn.classList.add('syncing');
            icon.classList.add('spinning');
            text.textContent = 'Syncing...';

            try {
                const response = await fetch('/api/project/sync', {
                    method: 'POST'
                });

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(data.detail || 'Failed to sync');
                }

                projectData = data;
                renderAllTabs(data);

                // Update last synced
                document.getElementById('last-synced').textContent =
                    `Last synced: ${new Date().toLocaleString()}`;

                // Show success toast
                successToast.classList.add('show');
                setTimeout(() => successToast.classList.remove('show'), 3000);

            } catch (error) {
                console.error('Error syncing project:', error);
                showToast(error.message || 'Failed to sync project', 'error');
            } finally {
                syncBtn.disabled = false;
                syncBtn.classList.remove('syncing');
                icon.classList.remove('spinning');
                text.textContent = 'Sync';
            }
        }

        // Show error
        function showError(message) {
            ['overview', 'broker', 'strategy'].forEach(tab => {
                document.getElementById(`${tab}-content`).innerHTML = `
                    <div class="section">
                        <div class="info-item">
                            <div class="info-label">Error</div>
                            <div class="info-value status-inactive">${message}</div>
                        </div>
                    </div>
                `;
            });
        }

        // Show toast notification (works for both success and error)
        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `toast ${type} show`;

            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }

        // Initialize - use initNavbar() for dual navbar
        (async () => {
            try {
                initNavbar();
                await loadProjectData();

                // Switch to tab from URL parameter
                const initialTab = getInitialTab();
                if (initialTab !== 'overview') {
                    switchTab(initialTab);
                }
            } catch (error) {
                console.error('Initialization error:', error);
                window.location.href = '/login';
            }
        })();
    """
