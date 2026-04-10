"""Trading Calendar page using FastHTML components."""

from fasthtml.common import (
    H1,
    H2,
    Body,
    Button,
    Div,
    Head,
    Html,
    Label,
    Link,
    Meta,
    Option,
    P,
    Script,
    Select,
    Span,
    Style,
    Title,
    to_xml,
)

from .components import confirmation_modal, get_modal_styles


def trading_calendar_page_html(user_name: str) -> str:
    """Render the trading calendar page.

    This renders the same UI as templates/trading_calendar.html but using FastHTML components.
    """
    page = Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Trading Calendar - ProAlgoTrader"),
            Link(rel="stylesheet", href="/static/css/shared.css?v=3"),
            Style(_trading_calendar_styles()),
        ),
        Body(
            # Old navbar container (for OLD routes)
            # FastHTML navbar container (for FASTHTML routes)
            Div(id="navbar-container"),
            # Main Content
            Div(
                # Page Header
                Div(
                    H1("Trading Calendar", cls="page-title"),
                    Div(
                        Div("Loading...", cls="sync-info", id="sync-info"),
                        Button(
                            svg_sync_icon(cls="sync-icon", id="sync-icon"),
                            Span("Sync", id="sync-text"),
                            cls="btn-sync",
                            id="sync-btn",
                            onclick="showSyncModal()",
                        ),
                        cls="header-actions",
                    ),
                    cls="page-header",
                ),
                # Stats
                Div(
                    Div(
                        Div("0", cls="stat-value", id="total-days"),
                        Div("Total Days", cls="stat-label"),
                        cls="stat-card",
                    ),
                    Div(
                        Div("0", cls="stat-value", id="trading-days"),
                        Div("Trading Days", cls="stat-label"),
                        cls="stat-card",
                    ),
                    Div(
                        Div("0", cls="stat-value", id="holidays"),
                        Div("Holidays", cls="stat-label"),
                        cls="stat-card",
                    ),
                    Div(
                        Div("0", cls="stat-value", id="weekends"),
                        Div("Weekends", cls="stat-label"),
                        cls="stat-card",
                    ),
                    cls="stats-grid",
                    id="stats-grid",
                ),
                # Calendar Table
                Div(
                    H2("Calendar Entries"),
                    Div(
                        Div(
                            Label("Per page:", for_="per-page"),
                            Select(
                                Option("10", value="10", selected=True),
                                Option("25", value="25"),
                                Option("50", value="50"),
                                Option("100", value="100"),
                                id="per-page",
                                onchange="changePerPage()",
                            ),
                            cls="per-page-selector",
                        ),
                        cls="controls-row",
                    ),
                    # Calendar content - initial loading state
                    Div(
                        Div(
                            Div(cls="spinner"),
                            P("Loading calendar..."),
                            cls="loading",
                        ),
                        id="calendar-content",
                    ),
                    # Pagination
                    Div(
                        Button("← Previous", id="prev-btn", onclick="prevPage()"),
                        Div(
                            "Page ",
                            Span("1", id="current-page"),
                            " of ",
                            Span("1", id="total-pages"),
                            " (",
                            Span("0", id="showing-count"),
                            " of ",
                            Span("0", id="total-count"),
                            " entries)",
                            cls="page-info",
                        ),
                        Button("Next →", id="next-btn", onclick="nextPage()"),
                        cls="pagination",
                        id="pagination",
                        style="display: none;",
                    ),
                    cls="card",
                ),
                cls="main-content",
            ),
            # Toast notification
            Div("", cls="toast", id="toast"),
            # Sync Confirmation Modal
            confirmation_modal(
                modal_id="sync-modal",
                title="Sync Trading Calendar?",
                message="This will fetch the latest trading calendar from NSE.\n\nThis action will update your local database with new calendar data.",
                submit_text="Sync",
                submit_onclick="confirmSync()",
                cancel_onclick="closeSyncModal()",
            ),
            # Scripts
            Script(src="/static/js/navbar.js?v=16"),
            Script(_trading_calendar_script()),
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


def _trading_calendar_styles() -> str:
    """Return the trading calendar CSS styles."""
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

        .header-actions {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .sync-info {
            font-size: 12px;
            color: #666;
        }

        .card {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }

        .card h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
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

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        .calendar-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .calendar-table th,
        .calendar-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        .calendar-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .calendar-table tr:hover {
            background: #f8f9fa;
        }

        .day-type {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .type-open {
            background: #d4edda;
            color: #155724;
        }

        .type-holiday {
            background: #f8d7da;
            color: #721c24;
        }

        .type-weekend {
            background: #fff3cd;
            color: #856404;
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

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
        }

        .stat-value {
            font-size: 32px;
            font-weight: 700;
        }

        .stat-label {
            font-size: 12px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }

        .empty-state h3 {
            margin-bottom: 15px;
            color: #333;
        }

        .empty-state p {
            margin-bottom: 20px;
        }

        .controls-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            gap: 20px;
            flex-wrap: wrap;
        }

        .per-page-selector {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .per-page-selector label {
            font-size: 14px;
            color: #666;
        }

        .per-page-selector select {
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
        }

        .per-page-selector select:focus {
            outline: none;
            border-color: #667eea;
        }

        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
        }

        .pagination button {
            padding: 10px 20px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }

        .pagination button:hover:not(:disabled) {
            background: #667eea;
            color: white;
        }

        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .pagination .page-info {
            padding: 10px 20px;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 14px;
            color: #333;
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
            z-index: 1000;
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


        .exchanges-list {
            font-size: 12px;
            color: #666;
        }

        .exchange-tag {
            display: inline-block;
            padding: 2px 6px;
            margin: 2px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 10px;
        }
    """
    )


def _trading_calendar_script() -> str:
    """Return the trading calendar JavaScript."""
    return """
        // Global state - MUST be declared before functions that use them
        let currentPage = 1;
        let perPage = 10;
        let totalCount = 0;
        let totalPages = 1;
        let pageEntries = [];
        let lastSynced = null;

        // Initialize - use initNavbar() for dual navbar
        (async () => {
            try {
                initNavbar(); // This loads user info via singleton
                await loadCalendar();
            } catch (error) {
                console.error('Initialization error:', error);
            }
        })();

        // Load trading calendar
        async function loadCalendar(page = currentPage, limit = perPage) {
            try {
                const response = await fetch(`/api/trading-calendar?page=${page}&per_page=${limit}`);

                if (!response.ok) {
                    throw new Error('Failed to load calendar');
                }

                const data = await response.json();
                pageEntries = data.calendar || [];
                totalCount = data.count || 0;
                totalPages = data.total_pages || 1;
                lastSynced = data.last_synced;

                // Update pagination state
                currentPage = data.page || 1;
                perPage = data.per_page || 10;

                updateStats();
                renderCalendar();
                updatePagination();
                updateSyncInfo();

            } catch (error) {
                console.error('Error loading calendar:', error);
                showToast('Failed to load calendar', 'error');
            }
        }

        // Update stats
        function updateStats() {
            document.getElementById('total-days').textContent = totalCount;

            // Fetch actual stats from API
            fetch('/api/trading-calendar/stats')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('trading-days').textContent = data.trading_days;
                        document.getElementById('holidays').textContent = data.holidays;
                        document.getElementById('weekends').textContent = data.weekends;
                    }
                })
                .catch(err => console.error('Error loading stats:', err));
        }

        // Update sync info
        function updateSyncInfo() {
            const syncInfo = document.getElementById('sync-info');
            if (lastSynced) {
                const date = new Date(lastSynced);
                syncInfo.textContent = `Last synced: ${date.toLocaleString()}`;
            } else if (totalCount === 0) {
                syncInfo.textContent = 'No data - click Sync to fetch from NSE';
            } else {
                syncInfo.textContent = `${totalCount} entries`;
            }
        }

        // Update pagination controls
        function updatePagination() {
            const pagination = document.getElementById('pagination');

            if (totalCount === 0) {
                pagination.style.display = 'none';
                return;
            }

            pagination.style.display = 'flex';

            document.getElementById('current-page').textContent = currentPage;
            document.getElementById('total-pages').textContent = totalPages;
            document.getElementById('showing-count').textContent = pageEntries.length;
            document.getElementById('total-count').textContent = totalCount;

            document.getElementById('prev-btn').disabled = currentPage <= 1;
            document.getElementById('next-btn').disabled = currentPage >= totalPages;
        }

        // Render calendar table
        function renderCalendar() {
            const content = document.getElementById('calendar-content');

            if (pageEntries.length === 0 && totalCount === 0) {
                content.innerHTML = `
                    <div class="empty-state">
                        <h3>No Calendar Data</h3>
                        <p>Click "Sync" to fetch trading calendar.</p>
                        <button class="btn-sync" onclick="showSyncModal()">
                            <svg class="sync-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M23 4v6h-6"></path>
                                <path d="M1 20v-6h6"></path>
                                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"></path>
                                <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"></path>
                            </svg>
                            Sync
                        </button>
                    </div>
                `;
                return;
            }

            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

            let html = `
                <table class="calendar-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Day</th>
                            <th>Description</th>
                            <th>Status</th>
                            <th>Closed Exchanges</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            pageEntries.forEach(entry => {
                const date = new Date(entry.date);
                const dayName = dayNames[date.getDay()];

                let typeClass = 'type-open';
                let typeText = 'Trading Day';

                if (entry.description === 'Weekend') {
                    typeClass = 'type-weekend';
                    typeText = 'Weekend';
                } else if (entry.closed_exchanges && entry.closed_exchanges !== '') {
                    typeClass = 'type-holiday';
                    typeText = 'Holiday';
                }

                // Parse closed exchanges
                const exchanges = entry.closed_exchanges ? entry.closed_exchanges.split(',').filter(e => e.trim()) : [];
                const exchangesHtml = exchanges.length > 0
                    ? exchanges.map(e => `<span class="exchange-tag">${e.trim()}</span>`).join('')
                    : '-';

                html += `
                    <tr>
                        <td><strong>${date.toLocaleDateString()}</strong></td>
                        <td>${dayName}</td>
                        <td>${entry.description}</td>
                        <td><span class="day-type ${typeClass}">${typeText}</span></td>
                        <td>${exchangesHtml}</td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;

            content.innerHTML = html;
        }

        // Pagination controls
        function prevPage() {
            if (currentPage > 1) {
                loadCalendar(currentPage - 1, perPage);
            }
        }

        function nextPage() {
            if (currentPage < totalPages) {
                loadCalendar(currentPage + 1, perPage);
            }
        }

        function changePerPage() {
            perPage = parseInt(document.getElementById('per-page').value);
            currentPage = 1;
            loadCalendar(1, perPage);
        }

        // Sync calendar from NSE API

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
            await syncCalendar();
        }

        async function syncCalendar() {
            const btn = document.getElementById('sync-btn');
            const icon = document.getElementById('sync-icon');
            const text = document.getElementById('sync-text');

            btn.disabled = true;
            btn.classList.add('syncing');
            icon.classList.add('spinning');
            text.textContent = 'Syncing...';

            try {
                const response = await fetch('/api/trading-calendar/sync', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Sync failed');
                }

                const data = await response.json();

                if (data.success) {
                    showToast(`${data.message} (Inserted: ${data.inserted}, Updated: ${data.updated})`, 'success');
                    // Reload calendar
                    await loadCalendar(currentPage, perPage);
                } else {
                    throw new Error(data.message || 'Sync failed');
                }

            } catch (error) {
                console.error('Error syncing calendar:', error);
                showToast(error.message || 'Failed to sync calendar', 'error');
            } finally {
                btn.disabled = false;
                btn.classList.remove('syncing');
                icon.classList.remove('spinning');
                text.textContent = 'Sync';
            }
        }

        // Show toast notification
        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = `toast ${type} show`;

            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
    """
