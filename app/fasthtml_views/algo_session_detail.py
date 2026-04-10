"""Algo Session Detail page using FastHTML components."""

from fasthtml.common import (
    H2,
    H3,
    Body,
    Button,
    Div,
    Head,
    Html,
    Link,
    Meta,
    P,
    Script,
    Span,
    Style,
    Title,
    to_xml,
)

from .components import confirmation_modal, get_modal_styles


def algo_session_detail_page_html(user_name: str, session_id: str) -> str:
    """Render the algo session detail page.

    This renders the same UI as templates/algo_session_detail.html but using FastHTML components.
    """
    page = Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Session Control - ProAlgoTrader"),
            Link(rel="stylesheet", href="/static/css/shared.css?v=3"),
            Style(_session_detail_styles()),
        ),
        Body(
            # Old navbar container (for OLD routes)
            # FastHTML navbar container (for FASTHTML routes)
            Div(id="navbar-container"),
            # Main Content
            Div(
                # Session Info Card
                Div(
                    Div(
                        Div(cls="spinner"),
                        P("Loading session information..."),
                        cls="loading",
                    ),
                    id="session-info",
                    cls="card",
                ),
                # Warning Container
                Div(id="warning-container"),
                # Live Start Confirmation Modal
                confirmation_modal(
                    modal_id="live-start-confirmation-modal",
                    title="⚠️ Start Live Trading?",
                    message="You are about to start a LIVE trading session.\n\nThis will trade with REAL MONEY.\n\nPlease ensure you understand the risks involved.",
                    cancel_text="Cancel",
                    submit_text="Start Live Trading",
                    cancel_onclick="closeLiveStartConfirmation()",
                    submit_onclick="confirmLiveStart()",
                ),
                # Live Stop Confirmation Modal
                confirmation_modal(
                    modal_id="live-stop-confirmation-modal",
                    title="⚠️ Stop Live Trading?",
                    message="You are about to STOP a LIVE trading session.\n\nThis will immediately halt all trading operations.\n\nMake sure you've managed your open positions properly.",
                    cancel_text="Cancel",
                    submit_text="Stop Live Trading",
                    cancel_onclick="closeLiveStopConfirmation()",
                    submit_onclick="confirmLiveStop()",
                ),
                # Control Card
                Div(
                    H2("Strategy Control"),
                    # Control Panel: Status + Action Button
                    Div(
                        Div(
                            Div("Current Status", cls="status-label"),
                            Div(
                                "IDLE",
                                cls="status-value status-idle",
                                id="status-value",
                            ),
                            Div(
                                "Click Start to begin",
                                cls="status-message",
                                id="status-message",
                            ),
                            Div("", cls="status-message", id="status-pid"),
                            cls="status-section",
                        ),
                        Div(
                            Button(
                                "▶️ Start",
                                cls="action-btn btn-start",
                                id="start-btn",
                                onclick="startStrategy()",
                            ),
                            id="action-section",
                        ),
                        cls="control-panel",
                    ),
                    # Real-time Logs
                    H3("Real-time Logs", style="margin-bottom: 15px; color: #333;"),
                    Div(
                        Div(
                            Span(
                                Span("", cls="connection-dot", id="connection-dot"),
                                Span("Disconnected", id="connection-status"),
                                cls="logs-status",
                            ),
                            Button(
                                "🗑️ Clear",
                                cls="clear-logs-btn",
                                onclick="clearLogs()",
                            ),
                            cls="logs-header",
                        ),
                        Div(
                            id="logs-container",
                            cls="logs-container",
                        ),
                        style="margin-top: 0;",
                    ),
                    cls="card",
                ),
                cls="main-content",
            ),
            # Scripts
            Script(src="/static/js/navbar.js?v=16"),
            Script(_session_detail_script(session_id)),
        ),
    )

    return to_xml(page)


def _session_detail_styles() -> str:
    """Return the session detail CSS styles matching the original template."""
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
            max-width: 1000px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        /* Control Panel */
        .control-panel {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        .status-section {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .status-label {
            color: #6c757d;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .status-value {
            font-size: 24px;
            font-weight: 700;
        }
        .status-idle { color: #6c757d; }
        .status-running { color: #28a745; }
        .status-stopped { color: #dc3545; }
        .status-message {
            font-size: 14px;
            color: #666;
        }
        .action-section {
            display: flex;
            align-items: center;
        }
        .action-btn {
            padding: 15px 40px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            min-width: 150px;
        }
        .action-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .btn-start {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }
        .btn-stop {
            background: linear-gradient(135deg, #dc3545 0%, #ff6b6b 100%);
            color: white;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
        .mode-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .mode-live {
            background: #d4edda;
            color: #155724;
        }
        .mode-paper {
            background: #fff3cd;
            color: #856404;
        }
        .mode-backtest {
            background: #d1ecf1;
            color: #0c5460;
        }
        button {
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
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
        .error-message {
            background: #fee;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            border-radius: 8px;
            color: #c0392b;
        }
        .warning-message {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            color: #856404;
            margin-bottom: 20px;
        }
        .warning-message strong {
            display: block;
            margin-bottom: 10px;
        }
        /* Logs styles */
        .logs-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            background: #1e1e1e;
            color: #d4d4d4;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.5;
        }
        .log-entry {
            padding: 8px 15px;
            border-bottom: 1px solid #333;
        }
        .log-entry:last-child {
            border-bottom: none;
        }
        .log-info { color: #4fc3f7; }
        .log-warning { color: #ffb74d; }
        .log-error { color: #ef5350; background: rgba(239, 83, 80, 0.1); }
        .log-debug { color: #9e9e9e; }
        .log-system { color: #81c784; }
        .log-timestamp {
            color: #757575;
            margin-right: 10px;
        }
        .log-level {
            font-weight: bold;
            margin-right: 10px;
            text-transform: uppercase;
        }
        .log-message {
            color: #d4d4d4;
        }
        .log-event {
            color: #ba68c8;
            margin-left: 10px;
            font-style: italic;
        }
        .logs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding: 10px 0;
        }
        .logs-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }
        .connection-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6c757d;
            transition: all 0.3s ease;
        }
        .connection-dot.connected {
            background: #28a745;
            box-shadow: 0 0 8px rgba(40, 167, 69, 0.5);
        }
        .clear-logs-btn {
            padding: 6px 12px;
            font-size: 12px;
            background: #6c757d;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.2s ease;
            width: auto;
            flex: none;
        }
        .clear-logs-btn:hover {
            background: #5a6268;
        }
    """
    )


def _session_detail_script(session_id: str) -> str:
    """Return the session detail JavaScript matching the original template."""
    return f"""
        // Get session ID from URL
        const sessionId = '{session_id}';

        // State
        let websocket = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        // Update action button (show only Start OR Stop)
        function updateActionButton(isRunning) {{
            const actionSection = document.getElementById('action-section');

            if (isRunning) {{
                actionSection.innerHTML = `
                    <button class="action-btn btn-stop" id="stop-btn" onclick="stopStrategy()">
                        ⏹️ Stop
                    </button>
                `;
            }} else {{
                actionSection.innerHTML = `
                    <button class="action-btn btn-start" id="start-btn" onclick="startStrategy()">
                        ▶️ Start
                    </button>
                `;
            }}
        }}

        // WebSocket connection
        function connectWebSocket() {{
            // Don't connect if already connected or connecting
            if (websocket) {{
                if (websocket.readyState === WebSocket.OPEN) {{
                    return; // Already connected
                }}
                if (websocket.readyState === WebSocket.CONNECTING) {{
                    return; // Already connecting
                }}
            }}

            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws/algo-sessions/${{sessionId}}`;

            console.log(`[WebSocket] Connecting to session ${{sessionId}}...`);

            websocket = new WebSocket(wsUrl);

            websocket.onopen = function(event) {{
                console.log('[WebSocket] Connected');
                updateConnectionStatus(true);
                reconnectAttempts = 0;
            }};

            websocket.onmessage = function(event) {{
                try {{
                    const data = JSON.parse(event.data);
                    addLog(data.level, data.message, data.event);

                    // Update UI directly based on WebSocket events (no polling)
                    if (data.event === 'started') {{
                        console.log('[WebSocket] Strategy started');
                        updateStatusUI('running');
                    }} else if (data.event === 'completed') {{
                        console.log('[WebSocket] Strategy completed');
                        addLog('system', '✓ Strategy finished successfully');
                        updateStatusUI('stopped');
                    }} else if (data.event === 'error') {{
                        console.log('[WebSocket] Strategy error');
                        addLog('system', '✗ Strategy encountered an error');
                        updateStatusUI('stopped');
                    }}
                }} catch (error) {{
                    console.error('[WebSocket] Error parsing message:', error);
                }}
            }};

            websocket.onclose = function(event) {{
                console.log('[WebSocket] Disconnected');
                updateConnectionStatus(false);
                websocket = null; // Reset so we can reconnect

                // Try to reconnect after 5 seconds
                if (reconnectAttempts < maxReconnectAttempts) {{
                    setTimeout(() => {{
                        console.log('[WebSocket] Reconnecting...');
                        reconnectAttempts++;
                        connectWebSocket();
                    }}, 5000);
                }}
            }};

            websocket.onerror = function(error) {{
                console.error('[WebSocket] Error:', error);
                updateConnectionStatus(false);
            }};
        }}

        // Update connection status
        function updateConnectionStatus(connected) {{
            const dot = document.getElementById('connection-dot');
            const status = document.getElementById('connection-status');

            if (connected) {{
                dot.classList.add('connected');
                status.textContent = 'Connected';
            }} else {{
                dot.classList.remove('connected');
                status.textContent = 'Disconnected';
            }}
        }}

        // Add log entry
        function addLog(level, message, event = null) {{
            const container = document.getElementById('logs-container');
            const timestamp = new Date().toLocaleTimeString();

            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${{level}}`;

            let html = `<span class="log-timestamp">[${{timestamp}}]</span>`;
            html += `<span class="log-level">${{level}}</span>`;
            html += `<span class="log-message">${{escapeHtml(message)}}</span>`;

            if (event) {{
                html += `<span class="log-event">[${{event}}]</span>`;
            }}

            logEntry.innerHTML = html;
            container.appendChild(logEntry);

            // Auto-scroll to bottom
            container.scrollTop = container.scrollHeight;
        }}

        // Clear logs
        function clearLogs() {{
            console.log('[UI] Logs cleared');
            document.getElementById('logs-container').innerHTML = '';
        }}

        // Escape HTML
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        // Load session info
        async function loadSessionInfo() {{
            try {{
                const response = await fetch(`/api/algo-sessions/${{sessionId}}`);
                const data = await response.json();

                if (!response.ok || !data.success) {{
                    throw new Error(data.detail || 'Failed to load session info');
                }}

                renderSessionInfo(data.session);
            }} catch (error) {{
                console.error('Error loading session info:', error);
                document.getElementById('session-info').innerHTML = `
                    <div class="error-message">
                        <p><strong>Error:</strong> ${{error.message}}</p>
                    </div>
                `;
            }}
        }}

        // Render session info
        function renderSessionInfo(session) {{
            const modeClass = `mode-${{session.mode.toLowerCase()}}`;

            let html = `
                <h2>Session Details</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Mode</div>
                        <div class="info-value">
                            <span class="mode-badge ${{modeClass}}">${{session.mode}}</span>
                        </div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Timezone</div>
                        <div class="info-value">${{session.tz}}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Created</div>
                        <div class="info-value">${{formatDateTime(session.created_at)}}</div>
                    </div>
            `;

            if (session.mode === 'Backtest') {{
                html += `
                    <div class="info-item">
                        <div class="info-label">Start Date</div>
                        <div class="info-value">${{formatDate(session.backtest_start_date)}}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">End Date</div>
                        <div class="info-value">${{formatDate(session.backtest_end_date)}}</div>
                    </div>
                `;
            }}

            html += `
                </div>
            `;

            document.getElementById('session-info').innerHTML = html;
        }}

        // Format datetime
        function formatDateTime(datetime) {{
            if (!datetime) return 'N/A';
            const date = new Date(datetime);
            return date.toLocaleString();
        }}

        // Format date only
        function formatDate(dateStr) {{
            if (!dateStr) return 'N/A';
            return dateStr; // Already in YYYY-MM-DD format
        }}

        // Strategy controls
        let runningSessionInfo = null;

        // Update UI directly (no API call)
        function updateStatusUI(status) {{
            console.log('[updateStatusUI] Setting status to:', status);

            const statusValue = document.getElementById('status-value');
            const statusMessage = document.getElementById('status-message');
            const statusPid = document.getElementById('status-pid');

            // Update status text and color
            statusValue.textContent = status.toUpperCase();
            statusValue.className = 'status-value status-' + status;

            // Update message and button
            if (status === 'running') {{
                statusMessage.textContent = 'Strategy is running';
                statusPid.textContent = 'Process active';
                updateActionButton(true);
            }} else if (status === 'stopped') {{
                statusMessage.textContent = 'Strategy stopped';
                statusPid.textContent = 'Process terminated';
                updateActionButton(false);
            }}
        }}

        async function updateStatus() {{
            console.log('[updateStatus] Fetching status...');
            try {{
                // Check if any session is running
                const runningResponse = await fetch('/api/algo-sessions/running');

                // Check if unauthorized
                if (runningResponse.status === 401) {{
                    window.location.href = '/login';
                    return;
                }}

                const runningData = await runningResponse.json();
                console.log('[updateStatus] Running data:', runningData);

                // Then check this session's status
                const response = await fetch(`/api/algo-sessions/${{sessionId}}/status`);
                const data = await response.json();
                console.log('[updateStatus] Session status:', data);

                const statusValue = document.getElementById('status-value');
                const statusMessage = document.getElementById('status-message');
                const statusPid = document.getElementById('status-pid');

                // Check for warning (another session running)
                const warningDiv = document.getElementById('warning-container');

                if (runningData.running && runningData.session.id !== sessionId) {{
                    // Another session is running
                    warningDiv.innerHTML = `
                        <div class="warning-message">
                            <strong>⚠️ Another session is already running</strong>
                            <p>A ${{runningData.session.mode}} session (PID: ${{runningData.session.pid}}) is currently running.</p>
                            <p>Stop it before starting this session.</p>
                        </div>
                    `;
                }} else {{
                    warningDiv.innerHTML = '';
                }}

                console.log('[updateStatus] Setting status to:', data.status);
                statusValue.textContent = data.status.toUpperCase();
                statusValue.className = 'status-value status-' + data.status;

                statusMessage.textContent = data.message || '';

                if (data.pid) {{
                    statusPid.textContent = 'Process ID: ' + data.pid;
                }} else if (data.exit_code !== undefined) {{
                    statusPid.textContent = 'Exit Code: ' + data.exit_code;
                }} else {{
                    statusPid.textContent = '';
                }}

                // Update action button (show Start OR Stop)
                const isRunning = data.status === 'running';
                const anotherRunning = runningData.running && runningData.session.id !== sessionId;

                updateActionButton(isRunning);

                // If another session is running, disable the start button
                if (!isRunning && anotherRunning) {{
                    const startBtn = document.getElementById('start-btn');
                    if (startBtn) startBtn.disabled = true;
                }}
            }} catch (error) {{
                console.error('[updateStatus] Failed to fetch status:', error);
                // Don't show alert, just log error. User can click refresh to try again.
            }}
        }}

        async function startStrategy() {{
            // Clear logs from previous runs
            clearLogs();

            // Check if this is a Live session and show confirmation
            const sessionResponse = await fetch(`/api/algo-sessions/${{sessionId}}`);
            const sessionData = await sessionResponse.json();

            if (sessionData.success && sessionData.session.mode === 'Live') {{
                // Show live confirmation modal
                const modal = document.getElementById('live-start-confirmation-modal');
                modal.classList.add('active');
                return;
            }}

            // For Paper and Backtest, start directly
            await executeStartStrategy();
        }}

        function closeLiveStartConfirmation() {{
            const modal = document.getElementById('live-start-confirmation-modal');
            modal.classList.remove('active');
        }}

        async function confirmLiveStart() {{
            closeLiveStartConfirmation();
            await executeStartStrategy();
        }}

        async function executeStartStrategy() {{
            addLog('system', 'Starting strategy...');

            try {{
                // Ensure WebSocket is connected (reconnect if needed)
                if (!websocket || websocket.readyState !== WebSocket.OPEN) {{
                    connectWebSocket();
                }}

                const response = await fetch(`/api/algo-sessions/${{sessionId}}/start`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{}})
                }});
                const data = await response.json();

                if (response.ok) {{
                    addLog('info', 'Strategy started successfully', 'started');
                    await updateStatus();
                }} else {{
                    addLog('error', `Failed to start: ${{data.detail}}`);
                    alert('❌ Error: ' + data.detail);
                }}
            }} catch (error) {{
                addLog('error', `Failed to start: ${{error.message}}`);
                alert('❌ Failed to start: ' + error.message);
            }}
        }}

        async function stopStrategy() {{
            // Check if this is a Live session and show confirmation
            const sessionResponse = await fetch(`/api/algo-sessions/${{sessionId}}`);
            const sessionData = await sessionResponse.json();

            if (sessionData.success && sessionData.session.mode === 'Live') {{
                // Show live stop confirmation modal
                const modal = document.getElementById('live-stop-confirmation-modal');
                modal.classList.add('active');
                return;
            }}

            // For Paper and Backtest, stop directly
            await executeStopStrategy();
        }}

        function closeLiveStopConfirmation() {{
            const modal = document.getElementById('live-stop-confirmation-modal');
            modal.classList.remove('active');
        }}

        async function confirmLiveStop() {{
            closeLiveStopConfirmation();
            await executeStopStrategy();
        }}

        async function executeStopStrategy() {{
            addLog('system', 'Stopping strategy...');

            try {{
                const response = await fetch(`/api/algo-sessions/${{sessionId}}/stop`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }});
                const data = await response.json();

                if (response.ok) {{
                    addLog('info', 'Strategy stopped', 'stopped');
                    await updateStatus();
                }} else {{
                    addLog('error', `Failed to stop: ${{data.detail}}`);
                    alert('❌ Error: ' + data.detail);
                }}
            }} catch (error) {{
                addLog('error', `Failed to stop: ${{error.message}}`);
                alert('❌ Failed to stop: ' + error.message);
            }}
        }}

        // Initialize - use initNavbar() for dual navbar
        (async () => {{
            // Check authentication first
            try {{
                // Initialize shared navbar (handles auth check)
                initNavbar();

                // Connect WebSocket immediately
                connectWebSocket();

                // Load session info
                await loadSessionInfo();

                // Initial status check
                await updateStatus();
            }} catch (error) {{
                console.error('[Session Detail] Error:', error);
            }}
        }})();
    """
