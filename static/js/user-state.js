/**
 * Shared User State Management
 * Prevents duplicate API calls for user authentication
 */

// Global user state
let userState = {
    authenticated: false,
    user: null,
    loading: false,
    loaded: false
};

// Global promise to prevent duplicate requests
let userPromise = null;

/**
 * Get user info - singleton pattern to prevent duplicate calls
 * If already loaded, returns cached data
 * If currently loading, returns the same promise
 * If not loaded, makes one API call
 */
async function getUserInfo() {
    // If already loaded, return cached data
    if (userState.loaded) {
        return userState;
    }

    // If currently loading, return the same promise
    if (userPromise) {
        return userPromise;
    }

    // Start loading
    userState.loading = true;
    userPromise = fetch('/api/auth/user')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load user info');
            }
            return response.json();
        })
        .then(data => {
            if (data.authenticated && data.user) {
                userState = {
                    authenticated: true,
                    user: data.user,
                    loading: false,
                    loaded: true
                };
                return userState;
            } else {
                throw new Error('User not authenticated');
            }
        })
        .catch(error => {
            userState = {
                authenticated: false,
                user: null,
                loading: false,
                loaded: true
            };
            throw error;
        })
        .finally(() => {
            userPromise = null;
        });

    return userPromise;
}

/**
 * Load user info and update navbar
 * Uses singleton pattern to prevent duplicate calls
 */
async function loadNavbarUserInfo() {
    console.log('[UserState] Loading user info for navbar...');

    try {
        const state = await getUserInfo();

        // Update navbar
        const nameEl = document.getElementById('nav-user-name');
        const emailEl = document.getElementById('nav-user-email');

        if (nameEl) nameEl.textContent = state.user.name || 'Unknown';
        if (emailEl) emailEl.textContent = state.user.email || 'No email';

        return state;
    } catch (error) {
        console.error('[UserState] Error:', error);

        // Redirect to login on auth failure
        window.location.href = '/login';
        throw error;
    }
}

/**
 * Check if user is authenticated
 * Returns cached data if available, otherwise makes API call
 */
async function isAuthenticated() {
    try {
        const state = await getUserInfo();
        return state.authenticated;
    } catch (error) {
        return false;
    }
}

/**
 * Get current user (returns null if not loaded yet)
 */
function getCurrentUser() {
    return userState.user;
}

/**
 * Clear user state (for logout)
 */
function clearUserState() {
    userState = {
        authenticated: false,
        user: null,
        loading: false,
        loaded: false
    };
}

// Export functions for use in other scripts
window.loadNavbarUserInfo = loadNavbarUserInfo;
window.getUserInfo = getUserInfo;
window.isAuthenticated = isAuthenticated;
window.getCurrentUser = getCurrentUser;
window.clearUserState = clearUserState;
