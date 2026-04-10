"""Algo Sessions page using FastHTML components."""

from fasthtml.common import (
    H1,
    H2,
    Body,
    Button,
    Div,
    Form,
    Head,
    Html,
    Input,
    Label,
    Link,
    Meta,
    NotStr,
    Option,
    Script,
    Select,
    Span,
    Style,
    Title,
    to_xml,
)


def svg_plus_icon(**kwargs):
    """SVG plus icon using NotStr for proper rendering."""
    # Build icon class
    icon_cls = "plus-icon"
    if "cls" in kwargs:
        icon_cls = kwargs.pop("cls")

    # Build SVG with plus path
    svg_content = f"""<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="{icon_cls}">
  <line x1="12" y1="5" x2="12" y2="19"></line>
  <line x1="5" y1="12" x2="19" y2="12"></line>
</svg>"""

    # Add any additional attributes
    for key, value in kwargs.items():
        svg_content = svg_content.replace("<svg>", f'<svg {key}="{value}">', 1)

    return NotStr(svg_content)


def algo_sessions_page_html(user_name: str) -> str:
    """Render the algo sessions page.

    This renders the same UI as templates/algo_sessions.html but using FastHTML components.
    """
    page = Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Algo Sessions - ProAlgoTrader"),
            Link(rel="stylesheet", href="/static/css/shared.css?v=3"),
            Style(_algo_sessions_styles()),
        ),
        Body(
            # Old navbar container (for OLD routes)
            # FastHTML navbar container (for FASTHTML routes)
            Div(id="navbar-container"),
            # Main Content
            Div(
                Div(
                    H1("📊 Algo Sessions", cls="page-title"),
                    Button(
                        svg_plus_icon(cls="plus-icon"),
                        Span(" Create Session"),
                        cls="btn-create",
                        onclick="openCreateModal()",
                    ),
                    cls="page-header",
                ),
                Div(id="sessions-container"),
                cls="main-content",
            ),
            # Create Session Modal
            Div(
                Div(
                    Div(
                        H2("Create Algo Session", cls="modal-title"),
                        Button("×", cls="modal-close", onclick="closeCreateModal()"),
                        cls="modal-header",
                    ),
                    Div(id="modal-error", cls="error-message", style="display: none;"),
                    Form(
                        Div(
                            Label("Mode", cls="form-label", for_="mode"),
                            Select(
                                Option("Select mode", value=""),
                                Option("Live", value="Live"),
                                Option("Paper", value="Paper"),
                                Option("Backtest", value="Backtest"),
                                id="mode",
                                cls="form-select",
                                required=True,
                            ),
                            cls="form-group",
                        ),
                        Div(
                            Label("Timezone", cls="form-label", for_="tz"),
                            Select(
                                Option("Loading timezones...", value=""),
                                id="tz",
                                cls="form-select",
                                required=True,
                            ),
                            cls="form-group",
                        ),
                        Div(
                            Div(
                                Div(
                                    Label(
                                        "Start Date",
                                        cls="form-label",
                                        for_="backtest_start",
                                    ),
                                    Input(
                                        type="date",
                                        id="backtest_start",
                                        cls="form-input",
                                    ),
                                    cls="form-group",
                                ),
                                Div(
                                    Label(
                                        "End Date",
                                        cls="form-label",
                                        for_="backtest_end",
                                    ),
                                    Input(
                                        type="date", id="backtest_end", cls="form-input"
                                    ),
                                    cls="form-group",
                                ),
                                id="datetime-fields",
                                cls="datetime-fields",
                            ),
                            cls="form-group",
                        ),
                        Button(
                            "Create Session",
                            type="submit",
                            id="submitBtn",
                            cls="btn-submit",
                        ),
                        id="createSessionForm",
                        onsubmit="return handleSubmit(event)",
                    ),
                    cls="modal-content",
                ),
                id="createModal",
                cls="modal",
            ),
            # Scripts
            Script(src="/static/js/navbar.js?v=16"),
            Script(_algo_sessions_script()),
        ),
    )

    return to_xml(page)


def _algo_sessions_styles() -> str:
    """Return the algo sessions CSS styles matching the original template."""
    return """
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
            margin-bottom: 30px;
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

        .btn-create {
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

        .btn-create:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .plus-icon {
            width: 18px;
            height: 18px;
            display: inline-block;
            vertical-align: middle;
        }

        /* Table Styles */
        .sessions-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .sessions-table {
            width: 100%;
            border-collapse: collapse;
        }

        .sessions-table th {
            background: #f8f9fa;
            padding: 15px 20px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .sessions-table td {
            padding: 15px 20px;
            border-bottom: 1px solid #f0f0f0;
            color: #333;
        }

        .sessions-table tr:hover {
            background: #f8f9fa;
            cursor: pointer;
        }

        .sessions-table tr:last-child td {
            border-bottom: none;
        }

        .mode-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
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

        .status-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .status-running {
            background: #d4edda;
            color: #155724;
        }

        .status-stopped {
            background: #f8d7da;
            color: #721c24;
        }

        .status-idle {
            background: #e2e3e5;
            color: #383d41;
        }

        .btn-action {
            background: #6c757d;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: background 0.2s;
        }

        .btn-action:hover {
            background: #5a6268;
        }

        .btn-action:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .empty-state h2 {
            color: #333;
            margin-bottom: 10px;
        }

        .empty-state p {
            color: #666;
            margin-bottom: 20px;
        }

        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            animation: fadeIn 0.3s;
        }

        .modal.active {
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .modal-content {
            background-color: white;
            padding: 30px;
            border-radius: 15px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            animation: slideIn 0.3s;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }

        .modal-title {
            font-size: 24px;
            font-weight: 600;
            color: #333;
        }

        .modal-close {
            background: none;
            border: none;
            font-size: 28px;
            color: #999;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
        }

        .modal-close:hover {
            color: #333;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }

        .form-input, .form-select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.2s;
        }

        .form-input:focus, .form-select:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn-submit {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }

        .btn-submit:hover {
            transform: translateY(-2px);
        }

        .btn-submit:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .datetime-fields {
            display: none;
        }

        .datetime-fields.visible {
            display: block;
            animation: fadeIn 0.3s;
        }

        .error-message {
            background: #fee;
            color: #c0392b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
        }

        .pid-text {
            font-size: 12px;
            color: #666;
            margin-left: 5px;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .sessions-table {
                display: block;
                overflow-x: auto;
            }

            .page-header {
                flex-direction: column;
                gap: 15px;
            }
        }
    """


def _algo_sessions_script() -> str:
    """Return the algo sessions JavaScript matching the original template."""
    return """
        // State
        let sessions = [];
        let timezones = [];
        let websocket = null;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        // WebSocket connection
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/algo-sessions/events`;

            console.log('[WebSocket] Connecting to', wsUrl);

            websocket = new WebSocket(wsUrl);

            websocket.onopen = function(event) {
                console.log('[WebSocket] Connected');
                reconnectAttempts = 0;
            };

            websocket.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[WebSocket] Message received:', data);

                    // Handle different event types
                    if (data.event === 'started') {
                        loadSessions();
                    } else if (data.event === 'completed' || data.event === 'error') {
                        loadSessions();
                    } else if (data.event === 'stopped') {
                        loadSessions();
                    }
                } catch (error) {
                    console.error('[WebSocket] Error parsing message:', error);
                }
            };

            websocket.onclose = function(event) {
                console.log('[WebSocket] Disconnected');

                if (reconnectAttempts < maxReconnectAttempts) {
                    setTimeout(() => {
                        console.log('[WebSocket] Reconnecting...');
                        reconnectAttempts++;
                        connectWebSocket();
                    }, 5000);
                }
            };

            websocket.onerror = function(error) {
                console.error('[WebSocket] Error:', error);
            };
        }

        // Load timezones
        async function loadTimezones() {
            try {
                const response = await fetch('/static/data/timezones.json');
                const data = await response.json();
                timezones = data.timezones || [];
                populateTimezoneDropdown();
            } catch (error) {
                console.error('Error loading timezones:', error);
                const select = document.getElementById('tz');
                select.innerHTML = '<option value="Asia/Kolkata">Asia/Kolkata</option>';
            }
        }

        // Populate timezone dropdown
        function populateTimezoneDropdown() {
            const select = document.getElementById('tz');
            select.innerHTML = '';

            timezones.forEach(tz => {
                const option = document.createElement('option');
                option.value = tz.value;
                option.textContent = `${tz.city} (${tz.label})`;
                if (tz.value === 'Asia/Kolkata') {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }

        // Initialize - use initNavbar() which handles auth check
        (async () => {
            try {
                await loadTimezones();
                initNavbar(); // This loads user info via singleton
                await loadSessions();
                connectWebSocket();
            } catch (error) {
                console.error('Initialization error:', error);
                // Auth errors are handled by initNavbar()
            }
        })();

        // Load sessions
        async function loadSessions() {
            try {
                const response = await fetch('/api/algo-sessions');
                if (!response.ok) {
                    throw new Error('Failed to load sessions');
                }
                const data = await response.json();
                sessions = data.sessions || [];
                renderSessions();
            } catch (error) {
                console.error('Error loading sessions:', error);
                showError('Failed to load sessions. Please try again.');
            }
        }

        // Render sessions as table
        function renderSessions() {
            const container = document.getElementById('sessions-container');

            if (sessions.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h2>No Algo Sessions Yet</h2>
                        <p>Create your first algo session to get started</p>
                        <button class="btn-create" onclick="openCreateModal()">+ Create Session</button>
                    </div>
                `;
                return;
            }

            // Sort sessions: Live first, Paper second, Backtest last
            const modeOrder = { 'Live': 1, 'Paper': 2, 'Backtest': 3 };
            const sortedSessions = [...sessions].sort((a, b) => {
                return (modeOrder[a.mode] || 99) - (modeOrder[b.mode] || 99);
            });

            let tableRows = sortedSessions.map(session => {
                const modeClass = `mode-${session.mode.toLowerCase()}`;
                const statusClass = `status-${session.status}`;
                const statusText = session.status === 'running' && session.pid
                    ? `Running <span class="pid-text">(PID: ${session.pid})</span>`
                    : session.status.charAt(0).toUpperCase() + session.status.slice(1);

                let extraInfo = '';
                if (session.mode === 'Backtest') {
                    extraInfo = `${formatDate(session.backtest_start_date)} - ${formatDate(session.backtest_end_date)}`;
                }

                return `
                    <tr onclick="window.location.href='/algo-sessions/${session.id}'">
                        <td><span class="mode-badge ${modeClass}">${session.mode}</span></td>
                        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                        <td>${session.tz}</td>
                        <td>${extraInfo || '-'}</td>
                        <td>${formatDateTime(session.created_at)}</td>
                        <td>
                            <button class="btn-action" onclick="event.stopPropagation(); window.location.href='/algo-sessions/${session.id}'">
                                Manage
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');

            container.innerHTML = `
                <div class="sessions-card">
                    <table class="sessions-table">
                        <thead>
                            <tr>
                                <th>Mode</th>
                                <th>Status</th>
                                <th>Timezone</th>
                                <th>Backtest Dates</th>
                                <th>Created</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tableRows}
                        </tbody>
                    </table>
                </div>
            `;
        }

        // Format datetime
        function formatDateTime(datetime) {
            if (!datetime) return 'N/A';
            const date = new Date(datetime);
            return date.toLocaleString();
        }

        // Format date only
        function formatDate(dateStr) {
            if (!dateStr) return 'N/A';
            return dateStr;
        }

        // Modal functions
        function openCreateModal() {
            document.getElementById('createModal').classList.add('active');
            document.getElementById('modal-error').style.display = 'none';
            document.getElementById('tz').value = 'Asia/Kolkata';
        }

        function closeCreateModal() {
            document.getElementById('createModal').classList.remove('active');
            document.getElementById('createSessionForm').reset();
            document.getElementById('datetime-fields').classList.remove('visible');
        }

        // Handle mode change
        document.addEventListener('DOMContentLoaded', function() {
            const modeSelect = document.getElementById('mode');
            if (modeSelect) {
                modeSelect.addEventListener('change', function(e) {
                    const datetimeFields = document.getElementById('datetime-fields');
                    if (e.target.value === 'Backtest') {
                        datetimeFields.classList.add('visible');
                        document.getElementById('backtest_start').required = true;
                        document.getElementById('backtest_end').required = true;
                    } else {
                        datetimeFields.classList.remove('visible');
                        document.getElementById('backtest_start').required = false;
                        document.getElementById('backtest_end').required = false;
                    }
                });
            }
        });

        // Handle form submit
        async function handleSubmit(event) {
            event.preventDefault();

            const submitBtn = document.getElementById('submitBtn');
            const errorMsg = document.getElementById('modal-error');

            const mode = document.getElementById('mode').value;
            const tz = document.getElementById('tz').value;
            const backtestStart = document.getElementById('backtest_start').value;
            const backtestEnd = document.getElementById('backtest_end').value;

            if (mode === 'Backtest') {
                if (!backtestStart || !backtestEnd) {
                    errorMsg.textContent = 'Both start and end dates are required for Backtest mode';
                    errorMsg.style.display = 'block';
                    return false;
                }

                if (new Date(backtestStart) >= new Date(backtestEnd)) {
                    errorMsg.textContent = 'End date must be after start date';
                    errorMsg.style.display = 'block';
                    return false;
                }
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating...';
            errorMsg.style.display = 'none';

            try {
                const response = await fetch('/api/algo-sessions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        mode,
                        tz,
                        backtest_start_date: mode === 'Backtest' ? backtestStart : null,
                        backtest_end_date: mode === 'Backtest' ? backtestEnd : null
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    let errMsg = 'Failed to create session';
                    if (data.detail) {
                        if (typeof data.detail === 'string') {
                            errMsg = data.detail;
                        } else if (Array.isArray(data.detail)) {
                            errMsg = data.detail.map(err => err.msg).join(', ');
                        } else {
                            errMsg = JSON.stringify(data.detail);
                        }
                    }
                    throw new Error(errMsg);
                }

                closeCreateModal();
                await loadSessions();

            } catch (error) {
                console.error('Error creating session:', error);
                errorMsg.textContent = error.message;
                errorMsg.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Create Session';
            }

            return false;
        }

        function showError(message) {
            const container = document.getElementById('sessions-container');
            container.innerHTML = `
                <div class="empty-state">
                    <h2>Error</h2>
                    <p>${message}</p>
                </div>
            `;
        }
    """
