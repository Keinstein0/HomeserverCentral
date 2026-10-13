/**
 * loginForm — pure, importable helpers extracted from the inline <script>
 * in static/login.html.
 *
 * These power the static /login.html page served by Caddy: reading the
 * error/redirect/room query params that the Auth Gateway bounces back,
 * showing a human-readable error message, and pre-filling the login
 * form's hidden fields so the gateway's POST /login can send the user
 * back to the right place after authentication.
 *
 * The functions are intentionally DOM-light and framework-free so they can
 * be served as a plain ES module by Caddy's file_server AND unit-tested
 * with Vitest + happy-dom.
 */

/** Maps Auth Gateway error codes to user-facing messages. */
export const ERROR_MESSAGES = {
    missing_fields: 'Please enter both a username and password.',
    invalid_credentials: 'Invalid username or password.',
};

/**
 * Return the human-readable message for a gateway error code, or a
 * generic fallback when the code is null/unrecognised.
 * @param {string|null} code
 * @returns {string}
 */
export function getLoginError(code) {
    if (!code) return 'Something went wrong. Please try again.';
    return ERROR_MESSAGES[code] || 'Something went wrong. Please try again.';
}

/**
 * Parse the query string the Auth Gateway appends to the login redirect
 * (/login.html?error=...&redirect=...&room=...) into a structured object
 * with decoded values and sensible defaults.
 * @param {string} search  — window.location.search or any query string
 * @returns {{ error: string|null, redirect: string, room: string }}
 */
export function parseLoginQuery(search) {
    const params = new URLSearchParams(search);
    return {
        error: params.get('error'),
        redirect: params.get('redirect') || '/',
        room: params.get('room') || '',
    };
}

/**
 * Wire up the static login page: show the error box (if any) and pre-fill
 * the form's hidden redirect/room fields from the query string.
 *
 * Expects the DOM elements produced by static/login.html:
 *   #error, #redirect-field, #room-field
 *
 * @param {{ error: string|null, redirect: string, room: string }} parsed
 */
export function applyLoginState(parsed) {
    const errorBox = document.getElementById('error');
    if (errorBox && parsed.error) {
        errorBox.textContent = getLoginError(parsed.error);
        errorBox.style.display = 'block';
    }

    const redirectField = document.getElementById('redirect-field');
    if (redirectField) redirectField.value = parsed.redirect;

    const roomField = document.getElementById('room-field');
    if (roomField) roomField.value = parsed.room;
}

/**
 * Initialise the login page from the current window.location.search.
 * Called by the module script in static/login.html.
 */
export function initLoginPage(search = window.location.search) {
    const parsed = parseLoginQuery(search);
    applyLoginState(parsed);
}
