/**
 * Shared Navbar Component
 * Generates consistent navbar across all FastHTML pages
 */

// Render navbar
function renderNavbar(activePage = null) {
    const currentPath = window.location.pathname;
    console.log('[Navbar] Current path:', currentPath);

    // Determine which nav item is active
    const dashboardActive = currentPath === '/dashboard' || currentPath === '/' ? 'active' : '';
    const algoSessionsActive = currentPath.startsWith('/algo-sessions') ? 'active' : '';
    const baseSymbolsActive = currentPath === '/base-symbols' ? 'active' : '';
    const brokerSymbolsActive = currentPath === '/broker-symbols' ? 'active' : '';
    const tradingCalendarActive = currentPath === '/trading-calendar' ? 'active' : '';

    return `
        <nav class="navbar">
            <a href="/dashboard" class="navbar-brand">🚀 ProAlgoTrader</a>
            <div class="navbar-nav">
                <a href="/dashboard" class="nav-link ${dashboardActive}">Dashboard</a>
                <a href="/algo-sessions" class="nav-link ${algoSessionsActive}">Algo Sessions</a>
                <a href="/base-symbols" class="nav-link ${baseSymbolsActive}">Base Symbols</a>
                <a href="/broker-symbols" class="nav-link ${brokerSymbolsActive}">Broker Symbols</a>
                <a href="/trading-calendar" class="nav-link ${tradingCalendarActive}">Trading Calendar</a>
            </div>
            <div class="navbar-user">
                <div class="user-info">
                    <div class="user-name" id="nav-user-name">Loading...</div>
                    <div class="user-email" id="nav-user-email">Loading...</div>
                </div>
                <button class="btn-logout" onclick="logout('/login')">Logout</button>
            </div>
        </nav>
    `;
}

// Load user info and update navbar
async function loadNavbarUserInfo() {
    console.log('[Navbar] Loading user info...');
    try {
        const response = await fetch('/api/auth/user');
        console.log('[Navbar] Response status:', response.status);

        if (response.ok) {
            const data = await response.json();
            console.log('[Navbar] User data:', data);

            // API returns: { authenticated: true, user: { id, name, email } }
            if (data.authenticated && data.user) {
                const user = data.user;

                // Update navbar
                const nameEl = document.getElementById('nav-user-name');
                const emailEl = document.getElementById('nav-user-email');
                if (nameEl) nameEl.textContent = user.name || 'Unknown';
                if (emailEl) emailEl.textContent = user.email || 'No email';
            } else {
                console.log('[Navbar] User not authenticated, redirecting to login');
                window.location.href = '/login';
            }
        } else {
            console.log('[Navbar] Failed to load user info');
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('[Navbar] Error loading user info:', error);
        window.location.href = '/login';
    }
}

// Initialize navbar - single unified navbar for all FastHTML pages
function initNavbar(containerId = 'navbar-container') {
    console.log('[Navbar] Initializing navbar...');

    // Find or create navbar container
    let container = document.getElementById(containerId);
    if (!container) {
        // Create container at the beginning of body
        container = document.createElement('div');
        container.id = containerId;
        document.body.insertBefore(container, document.body.firstChild);
    }

    // Render navbar
    container.innerHTML = renderNavbar();

    // Load user info
    loadNavbarUserInfo();
}

// Initialize both old and new navbar containers (for backward compatibility during migration)
// This function can be removed once all pages are migrated to FastHTML
function initNavbarBoth(containerIdOld = 'navbar-container-old', containerIdFh = 'navbar-container-fh') {
    console.log('[Navbar] Initializing unified navbar...');

    // Just use initNavbar for the first available container
    const oldContainer = document.getElementById(containerIdOld);
    const fhContainer = document.getElementById(containerIdFh);

    // Prefer FastHTML container, fall back to old container
    const container = fhContainer || oldContainer;

    if (container) {
        container.innerHTML = renderNavbar();
        loadNavbarUserInfo();
    }
}

// Logout function
async function logout(redirectTo = '/login') {
    console.log('[Navbar] Logging out, redirect to:', redirectTo);
    try {
        await fetch('/oauth/logout', { method: 'GET' });
        window.location.href = redirectTo;
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = redirectTo;
    }
}
