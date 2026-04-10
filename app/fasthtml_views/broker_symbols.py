"""Broker Symbols page using FastHTML components."""

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


def broker_symbols_page_html(user_name: str) -> str:
    """Render the broker symbols page.

    This renders the same UI as templates/broker_symbols.html but using FastHTML components.
    """
    page = Html(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Broker Symbols - ProAlgoTrader"),
            Link(rel="stylesheet", href="/static/css/shared.css?v=3"),
            Style(_broker_symbols_styles()),
        ),
        Body(
            # Old navbar container (for OLD routes)
            # FastHTML navbar container (for FASTHTML routes)
            Div(id="navbar-container"),
            # Main Content
            Div(
                # Page Header
                Div(
                    H1("Broker Symbols", cls="page-title"),
                    Div(
                        Button(
                            svg_trash_icon(),
                            "Clear Cache",
                            cls="btn btn-danger",
                            onclick="showClearModal()",
                        ),
                        cls="header-actions",
                    ),
                    cls="page-header",
                ),
                # Stats
                Div(
                    Div(
                        Div("0", cls="stat-value", id="total-symbols"),
                        Div("Total Cached Symbols", cls="stat-label"),
                        cls="stat-card",
                    ),
                    Div(
                        Div("0", cls="stat-value", id="equity-count"),
                        Div("Equity", cls="stat-label"),
                        cls="stat-card",
                    ),
                    Div(
                        Div("0", cls="stat-value", id="futures-count"),
                        Div("Futures", cls="stat-label"),
                        cls="stat-card",
                    ),
                    Div(
                        Div("0", cls="stat-value", id="options-count"),
                        Div("Options", cls="stat-label"),
                        cls="stat-card",
                    ),
                    cls="stats-grid",
                    id="stats-grid",
                ),
                # Catalog Status
                Div(
                    H2("Catalog Status"),
                    Div(
                        Div(
                            Div(cls="spinner"),
                            P("Loading catalog status..."),
                            cls="loading",
                        ),
                        id="catalog-content",
                    ),
                    cls="card",
                ),
                # Broker Symbols List
                Div(
                    H2("Cached Symbols"),
                    Div(
                        Div(
                            Label("Per page:", for_="per-page"),
                            Select(
                                Option("25", value="25", selected=True),
                                Option("50", value="50"),
                                Option("100", value="100"),
                                Option("250", value="250"),
                                id="per-page",
                                onchange="changePerPage()",
                            ),
                            cls="per-page-selector",
                        ),
                        cls="controls-row",
                    ),
                    # Symbols content - initial loading state
                    Div(
                        Div(
                            Div(cls="spinner"),
                            P("Loading symbols..."),
                            cls="loading",
                        ),
                        id="symbols-content",
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
                            " symbols)",
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
            # Clear Cache Confirmation Modal
            confirmation_modal(
                modal_id="clear-modal",
                title="Clear Broker Symbols Cache?",
                message="This will delete all cached broker symbols from the local database.\n\nYou may need to re-resolve symbols after clearing.",
                submit_text="Clear Cache",
                submit_class="modal-btn modal-btn-confirm btn-danger",
                cancel_onclick="hideClearModal()",
                submit_onclick="clearCache()",
            ),
            # Update Catalog Confirmation Modal
            confirmation_modal(
                modal_id="update-modal",
                title="Update Catalog?",
                message="This will fetch the latest broker instrument catalog.\n\nThis action may take a few moments to complete.",
                submit_text="Update",
                submit_onclick="confirmUpdate()",
                cancel_onclick="closeUpdateModal()",
            ),
            # Toast notification
            Div("", cls="toast", id="toast"),
            # Scripts
            Script(src="/static/js/navbar.js?v=16"),
            Script(_broker_symbols_script()),
        ),
    )

    return to_xml(page)


def svg_trash_icon(**kwargs):
    """SVG trash icon using NotStr for proper SVG rendering."""
    from fasthtml.common import NotStr

    # Build icon class
    icon_cls = "icon"
    if "cls" in kwargs:
        icon_cls = kwargs.pop("cls")

    # Build SVG with proper paths
    svg_content = f"""<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="{icon_cls}">
  <path d="M3 6h18"/>
  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>
  <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
</svg>"""

    # Add any additional attributes
    for key, value in kwargs.items():
        svg_content = svg_content.replace("<svg", f'<svg {key}="{value}"', 1)

    return NotStr(svg_content)


def _broker_symbols_styles() -> str:
    """Return the broker symbols CSS styles."""
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

        .btn {
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary.syncing {
            background: #6c757d;
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-success {
            background: #28a745;
            color: white;
        }

        .btn-danger {
            background: #dc3545;
            color: white;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn .icon {
            width: 18px;
            height: 18px;
        }

        .btn .icon.spinning {
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 20px;
            border-radius: 12px;
            color: white;
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
        }

        .stat-label {
            font-size: 11px;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Catalog Status */
        .catalog-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 15px;
        }

        .catalog-item {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            border: 2px solid #e0e0e0;
        }

        .catalog-item.exists {
            border-color: #28a745;
        }

        .catalog-item.not-exists {
            border-color: #dc3545;
        }

        .catalog-item.stale {
            border-color: #ffc107;
        }

        .catalog-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }

        .catalog-broker {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            text-transform: capitalize;
        }

        .catalog-status {
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
        }

        .status-exists { background: #d4edda; color: #155724; }
        .status-not-exists { background: #f8d7da; color: #721c24; }
        .status-stale { background: #fff3cd; color: #856404; }

        .catalog-info {
            font-size: 13px;
            color: #666;
            margin-bottom: 15px;
        }

        .catalog-info-row {
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #e0e0e0;
        }

        .catalog-info-row:last-child {
            border-bottom: none;
        }

        .catalog-actions {
            display: flex;
            gap: 10px;
        }

        /* Symbols Table */
        .symbols-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .symbols-table th,
        .symbols-table td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        .symbols-table th {
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
            z-index: 10;
        }

        .symbols-table tr:hover {
            background: #f8f9fa;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .badge-equity { background: #e3f2fd; color: #1565c0; }
        .badge-future { background: #fff3e0; color: #ef6c00; }
        .badge-option { background: #fce4ec; color: #c2185b; }
        .badge-ce { background: #c8e6c9; color: #2e7d32; }
        .badge-pe { background: #ffcdd3; color: #c62828; }

        /* Table container for scrolling */
        .table-container {
            max-height: 600px;
            overflow-y: auto;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }

        /* Pagination */
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
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

        /* Toast */
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

        .toast.success { background: #27ae60; }
        .toast.error { background: #e74c3c; }
        .toast.info { background: #3498db; }

        /* Controls */
        .controls-row {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
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

        /* Empty State */
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

        /* Modal */


        .modal-actions {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
    """
    )


def _broker_symbols_script() -> str:
    """Return the broker symbols JavaScript."""
    return """
        // Initialize - use initNavbar() for dual navbar
        (async () => {
            try {
                initNavbar(); // This loads user info via singleton
                await loadCatalogStatus();
                await loadBrokerSymbols();
            } catch (error) {
                console.error('Initialization error:', error);
            }
        })();

        // Global state
        let currentPage = 1;
        let perPage = 25;
        let totalCount = 0;
        let totalPages = 1;
        let pageSymbols = [];
        let projectBroker = null;

        // Load project info to get connected broker
        async function loadProjectInfo() {
            try {
                const response = await fetch('/api/project/info');
                const data = await response.json();
                if (data.success && data.project?.broker) {
                    projectBroker = data.project.broker.broker_title;
                    return projectBroker;
                }
            } catch (error) {
                console.error('Error loading project info:', error);
            }
            return null;
        }

        // Load catalog status
        async function loadCatalogStatus() {
            const content = document.getElementById('catalog-content');
            const broker = await loadProjectInfo();

            if (!broker) {
                content.innerHTML = `
                    <div class="catalog-grid">
                        <div class="catalog-item not-exists">
                            <div class="catalog-header">
                                <span class="catalog-broker">No Broker Connected</span>
                                <span class="catalog-status status-not-exists">Not Configured</span>
                            </div>
                            <div class="catalog-info">
                                <div class="catalog-info-row">
                                    <span>Status:</span>
                                    <span>Connect a broker in project settings</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                return;
            }

            try {
                const response = await fetch(`/api/broker-symbols/${broker}/catalog/info`);
                const data = await response.json();

                if (data.success) {
                    const exists = data.exists;
                    const isFresh = data.is_fresh;
                    const age = data.age_hours;
                    const catalog = data.catalog;

                    let statusClass, statusText;
                    if (!exists) {
                        statusClass = 'not-exists';
                        statusText = 'Not Downloaded';
                    } else if (!isFresh) {
                        statusClass = 'stale';
                        statusText = `Stale (${age?.toFixed(1) || '?'}h old)`;
                    } else {
                        statusClass = 'exists';
                        statusText = `Fresh (${age?.toFixed(1) || '?'}h old)`;
                    }

                    const brokerName = broker.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase());

                    content.innerHTML = `
                        <div class="catalog-grid">
                            <div class="catalog-item ${statusClass}">
                                <div class="catalog-header">
                                    <span class="catalog-broker">${brokerName}</span>
                                    <span class="catalog-status status-${statusClass}">${statusText}</span>
                                </div>
                                <div class="catalog-info">
                                    ${exists ? `
                                        <div class="catalog-info-row">
                                            <span>Instruments:</span>
                                            <span>${catalog?.row_count?.toLocaleString() || '-'}</span>
                                        </div>
                                        <div class="catalog-info-row">
                                            <span>Size:</span>
                                            <span>${catalog?.size_mb || '-'} MB</span>
                                        </div>
                                        <div class="catalog-info-row">
                                            <span>Last Sync:</span>
                                            <span>${catalog?.modified ? new Date(catalog.modified).toLocaleString() : '-'}</span>
                                        </div>
                                    ` : `
                                        <div class="catalog-info-row">
                                            <span>Status:</span>
                                            <span>Click Update to download catalog</span>
                                        </div>
                                    `}
                                </div>
                                <div class="catalog-actions">
                                    <button class="btn btn-primary" onclick=\"showUpdateModal('${broker}')\" id="update-btn-${broker}">
                                        <svg class="icon" id="update-icon-${broker}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <path d="M23 4v6h-6"></path>
                                            <path d="M1 20v-6h6"></path>
                                            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"></path>
                                            <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"></path>
                                        </svg>
                                        <span id="update-text-${broker}">Update Catalog</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading catalog status:', error);
                content.innerHTML = `
                    <div class="catalog-grid">
                        <div class="catalog-item not-exists">
                            <div class="catalog-header">
                                <span class="catalog-broker">Error</span>
                                <span class="catalog-status status-not-exists">Failed to Load</span>
                            </div>
                            <div class="catalog-info">
                                <div class="catalog-info-row">
                                    <span>Status:</span>
                                    <span>Failed to load catalog status</span>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }
        }

        // Update catalog
        // Track which broker is being updated
        let currentUpdateBroker = null;

        // Show update confirmation modal
        function showUpdateModal(broker) {
            currentUpdateBroker = broker;
            document.getElementById('update-modal').classList.add('active');
        }

        // Close update modal
        function closeUpdateModal() {
            currentUpdateBroker = null;
            document.getElementById('update-modal').classList.remove('active');
        }

        // Confirm and execute update
        async function confirmUpdate() {
            if (currentUpdateBroker) {
                const broker = currentUpdateBroker;  // Save before closing modal
                closeUpdateModal();
                await updateCatalog(broker);
            }
        }

        async function updateCatalog(broker) {
            const btn = document.getElementById(`update-btn-${broker}`);
            const text = document.getElementById(`update-text-${broker}`);
            const icon = document.getElementById(`update-icon-${broker}`);

            btn.disabled = true;
            btn.classList.add('syncing');
            icon.classList.add('spinning');
            text.textContent = 'Updating...';

            try {
                const response = await fetch(`/api/broker-symbols/${broker}/sync-catalog?force=true`, {
                    method: 'POST'
                });

                const data = await response.json();

                if (response.ok && (data.status === 'success' || data.status === 'skipped')) {
                    showToast(`${broker}: ${data.message}`, 'success');
                    await loadCatalogStatus();
                } else {
                    throw new Error(data.detail || data.message || 'Failed to update catalog');
                }
            } catch (error) {
                console.error(`Error updating catalog for ${broker}:`, error);
                showToast(`Failed to update ${broker}: ${error.message}`, 'error');
            } finally {
                btn.disabled = false;
                btn.classList.remove('syncing');
                icon.classList.remove('spinning');
                text.textContent = 'Update Catalog';
            }
        }

        // Load broker symbols
        async function loadBrokerSymbols() {
            const url = `/api/broker-symbols/list?page=${currentPage}&per_page=${perPage}`;

            try {
                const response = await fetch(url);
                const data = await response.json();

                if (data.success !== false) {
                    pageSymbols = data.broker_symbols || [];
                    totalCount = data.count || 0;
                    totalPages = data.total_pages || 1;

                    updateStats();
                    renderSymbols();
                    updatePagination();
                } else {
                    throw new Error(data.message || 'Failed to load');
                }
            } catch (error) {
                console.error('Error loading broker symbols:', error);
                showToast('Failed to load broker symbols', 'error');
            }
        }

        // Update stats
        function updateStats() {
            fetch('/api/broker-symbols/stats')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('total-symbols').textContent = data.total || 0;
                        document.getElementById('equity-count').textContent = data.equity || 0;
                        document.getElementById('futures-count').textContent = data.futures || 0;
                        document.getElementById('options-count').textContent = data.options || 0;
                    }
                })
                .catch(err => console.error('Error loading stats:', err));
        }

        // Render symbols table
        function renderSymbols() {
            const content = document.getElementById('symbols-content');

            if (pageSymbols.length === 0 && totalCount === 0) {
                content.innerHTML = `
                    <div class="empty-state">
                        <h3>No Broker Symbols Found</h3>
                        <p>No resolved symbols in the cache. Symbols will appear here after they are resolved through the trading system.</p>
                    </div>
                `;
                document.getElementById('pagination').style.display = 'none';
                return;
            }

            let html = `
                <div class="table-container">
                    <table class="symbols-table">
                        <thead>
                            <tr>
                                <th>Base Symbol</th>
                                <th>Segment</th>
                                <th>Expiry</th>
                                <th>Strike</th>
                                <th>Type</th>
                                <th>Symbol Name</th>
                                <th>Token</th>
                                <th>Lot</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            pageSymbols.forEach(symbol => {
                const segmentClass = `badge-${symbol.segment_type.toLowerCase()}`;
                const optionTypeHtml = symbol.option_type
                    ? `<span class="badge badge-${symbol.option_type.toLowerCase()}">${symbol.option_type}</span>`
                    : '-';

                const expiryHtml = symbol.expiry_date
                    ? `${symbol.expiry_date}<br><small style="color:#666">${symbol.expiry_period || ''}</small>`
                    : '-';

                html += `
                    <tr>
                        <td><strong>${symbol.base_symbol_value || symbol.base_symbol_id?.substring(0, 8) || '-'}</strong></td>
                        <td><span class="badge ${segmentClass}">${symbol.segment_type}</span></td>
                        <td>${expiryHtml}</td>
                        <td>${symbol.strike_price || '-'}</td>
                        <td>${optionTypeHtml}</td>
                        <td><code style="font-size: 12px;">${symbol.symbol_name || '-'}</code></td>
                        <td><code style="font-size: 11px;">${symbol.exchange_token || symbol.symbol_token || '-'}</code></td>
                        <td>${symbol.lot_size || '-'}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
            `;

            content.innerHTML = html;
        }

        // Pagination
        function updatePagination() {
            const pagination = document.getElementById('pagination');

            if (totalCount === 0) {
                pagination.style.display = 'none';
                return;
            }

            pagination.style.display = 'flex';
            document.getElementById('current-page').textContent = currentPage;
            document.getElementById('total-pages').textContent = totalPages;
            document.getElementById('showing-count').textContent = pageSymbols.length;
            document.getElementById('total-count').textContent = totalCount;
            document.getElementById('per-page').value = perPage;

            document.getElementById('prev-btn').disabled = currentPage <= 1;
            document.getElementById('next-btn').disabled = currentPage >= totalPages;
        }

        function prevPage() {
            if (currentPage > 1) {
                currentPage--;
                loadBrokerSymbols();
            }
        }

        function nextPage() {
            if (currentPage < totalPages) {
                currentPage++;
                loadBrokerSymbols();
            }
        }

        function changePerPage() {
            perPage = parseInt(document.getElementById('per-page').value);
            currentPage = 1;
            loadBrokerSymbols();
        }

        // Clear cache modal
        function showClearModal() {
            document.getElementById('clear-modal').classList.add('show');
        }

        function hideClearModal() {
            document.getElementById('clear-modal').classList.remove('show');
        }

        // Clear cache
        async function clearCache() {
            // Get the submit button from the modal
            const submitBtn = document.querySelector('#clear-modal .modal-btn-confirm');
            const originalText = submitBtn.textContent;

            submitBtn.disabled = true;
            submitBtn.textContent = 'Clearing...';

            try {
                const response = await fetch('/api/broker-symbols/clear', {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    hideClearModal();
                    showToast(`Cleared ${data.count} symbols from cache`, 'success');
                    loadBrokerSymbols();
                } else {
                    throw new Error(data.detail || 'Failed to clear cache');
                }
            } catch (error) {
                console.error('Error clearing cache:', error);
                hideClearModal();
                showToast(error.message || 'Failed to clear cache', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
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
