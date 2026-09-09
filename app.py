from flask import Flask, request, redirect, jsonify, render_template_string, session
import secrets
import time
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ============================================================
# CONFIGURATION
# ============================================================

AUTH_CODE_TTL = 120          # Authorization code lifetime
TOKEN_TTL = 3600             # Access token lifetime

# ============================================================
# IN-MEMORY STORE
# ============================================================

class Store:
    def __init__(self):
        self.CLIENTS = {}
        self.USERS = {}
        self.AUTH_CODES = {}
        self.ACCESS_TOKENS = {}

    def generate_token(self):
        return secrets.token_urlsafe(32)

    def store_access_token(self, token, client_id, scope, user):
        self.ACCESS_TOKENS[token] = {
            "client_id": client_id,
            "scope": scope,
            "user": user,
            "expires_at": time.time() + TOKEN_TTL
        }


store = Store()

# ============================================================
# DEMO USERS
# ============================================================

store.USERS = {
    "alice": {
        "password": "pass123",
        "name": "Alice",
        "email": "alice@example.com"
    },
    "bob": {
        "password": "letmein",
        "name": "Bob",
        "email": "bob@example.com"
    },
    "rohith": {
        "password": "rohith99",
        "name": "Rohith",
        "email": "rohith@example.com"
    }
}

# ============================================================
# DEMO CLIENT
# ============================================================

CLIENT_ID = "lab-client-001"
CLIENT_SECRET = "lab-secret-123"

store.CLIENTS[CLIENT_ID] = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "name": "OAuth Virtual Lab Client",
    "allowed_scopes": [
        "profile",
        "email",
        "read"
    ],
    "redirect_uris": [
        "http://127.0.0.1:5000/callback",
        "http://localhost:5000/callback"
    ]
}

# ============================================================
# COMMON CSS
# ============================================================

BASE_CSS = """
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Inter, Arial, sans-serif;
    background:
        radial-gradient(circle at top left, #1e293b, transparent 40%),
        radial-gradient(circle at bottom right, #312e81, transparent 40%),
        #080b14;
    color: #f8fafc;
    min-height: 100vh;
}

button, input {
    font-family: inherit;
}

a {
    color: inherit;
    text-decoration: none;
}

.container {
    width: min(1100px, calc(100% - 32px));
    margin: auto;
}

.card {
    width: min(460px, calc(100% - 32px));
    margin: 60px auto;
    padding: 32px;
    background: rgba(15, 23, 42, 0.88);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 18px;
    box-shadow: 0 25px 70px rgba(0,0,0,.4);
}

.lock-icon {
    text-align: center;
    font-size: 45px;
    margin-bottom: 15px;
}

h1 {
    text-align: center;
    margin: 0 0 10px;
    font-size: 28px;
}

.subtitle {
    text-align: center;
    color: rgba(255,255,255,.55);
    line-height: 1.5;
}

.app-badge {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 13px;
    margin: 22px 0;
    border-radius: 10px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.08);
}

.scope-box {
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 10px;
    background: rgba(255,255,255,.04);
}

.scope-box p {
    margin-top: 0;
    color: rgba(255,255,255,.5);
    font-size: 13px;
}

.scope-tag {
    display: inline-block;
    padding: 5px 9px;
    margin: 3px;
    border-radius: 6px;
    background: rgba(102,126,234,.18);
    border: 1px solid rgba(102,126,234,.35);
    color: #c7d2fe;
    font-size: 12px;
}

label {
    display: block;
    margin: 14px 0 7px;
    font-size: 13px;
    color: rgba(255,255,255,.7);
}

input {
    width: 100%;
    padding: 12px 14px;
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 9px;
    background: rgba(255,255,255,.05);
    color: white;
    outline: none;
}

input:focus {
    border-color: #667eea;
}

.error-msg {
    background: rgba(239,68,68,.15);
    border: 1px solid rgba(239,68,68,.4);
    border-radius: 8px;
    padding: 10px 14px;
    color: #fca5a5;
    font-size: 13px;
    margin-bottom: 18px;
}

.btn {
    width: 100%;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    border-radius: 10px;
    padding: 13px;
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity .2s, transform .1s;
    margin-top: 18px;
}

.btn:hover {
    opacity: .9;
}

.btn:active {
    transform: scale(.98);
}

.btn-row {
    display: flex;
    gap: 12px;
}

.btn-deny {
    background: #7f1d1d;
}

.btn-approve {
    background: #047857;
}

.hint {
    margin-top: 20px;
    padding: 12px;
    background: rgba(255,255,255,.04);
    border-radius: 8px;
    font-size: 12px;
    color: rgba(255,255,255,.35);
    line-height: 1.6;
}

.hint strong {
    color: rgba(255,255,255,.55);
}

.divider {
    border-top: 1px solid rgba(255,255,255,.08);
    margin: 24px 0;
}

.server-badge {
    text-align: center;
    color: rgba(255,255,255,.25);
    font-size: 11px;
}

header {
    padding: 30px 0 15px;
}

header h1 {
    text-align: left;
    font-size: 32px;
}

header p {
    color: #94a3b8;
}

.status {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 20px;
    background: rgba(239,68,68,.12);
    color: #fca5a5;
    font-size: 12px;
}

.status.online {
    background: rgba(16,185,129,.12);
    color: #6ee7b7;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
}

.workflow {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin: 25px 0;
}

.step {
    padding: 15px;
    border: 1px solid rgba(255,255,255,.08);
    background: rgba(255,255,255,.04);
    border-radius: 12px;
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
}

.step.active {
    border-color: #818cf8;
    color: #fff;
    background: rgba(99,102,241,.15);
}

.step-number {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 5px;
}

.grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}

.panel {
    background: rgba(15,23,42,.8);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 15px;
    padding: 20px;
}

.panel h2 {
    margin-top: 0;
    font-size: 18px;
}

.panel p {
    color: #94a3b8;
    line-height: 1.6;
    font-size: 14px;
}

.info-row {
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255,255,255,.06);
    font-size: 13px;
}

.info-row span:first-child {
    color: #94a3b8;
}

.info-row span:last-child {
    text-align: right;
    max-width: 60%;
    word-break: break-word;
}

.security-test {
    border: 1px solid rgba(255,255,255,.1);
    background: rgba(255,255,255,.05);
    color: white;
    padding: 9px 12px;
    border-radius: 8px;
    cursor: pointer;
    margin: 4px;
}

.security-test:hover {
    background: rgba(255,255,255,.1);
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}

th, td {
    text-align: left;
    padding: 10px;
    border-bottom: 1px solid rgba(255,255,255,.06);
}

th {
    color: #94a3b8;
}

.badge {
    padding: 4px 7px;
    border-radius: 5px;
    font-size: 10px;
}

.good {
    background: rgba(16,185,129,.15);
    color: #6ee7b7;
}

.bad {
    background: rgba(239,68,68,.15);
    color: #fca5a5;
}

.lab-footer {
    display: flex;
    justify-content: space-between;
    width: min(1100px, calc(100% - 32px));
    margin: 30px auto;
    color: #64748b;
    font-size: 11px;
}

.toast {
    position: fixed;
    left: 50%;
    bottom: 25px;
    padding: 10px 14px;
    background: #f8fafc;
    color: #0f172a;
    font-size: 14px;
    border-radius: 8px;
    opacity: 0;
    transform: translate(-50%, 12px);
    transition: opacity .2s, transform .2s;
}

.toast.show {
    opacity: 1;
    transform: translate(-50%, 0);
}

@media (max-width: 800px) {
    .workflow {
        grid-template-columns: repeat(3, 1fr);
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .lab-footer {
        flex-direction: column;
        gap: 8px;
    }
}
"""

# ============================================================
# LOGIN PAGE
# ============================================================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>OAuth2 Login</title>
    <style>{{ css|safe }}</style>
</head>

<body>

<div class="card">

    <div class="lock-icon">🔐</div>

    <h1>Sign in to continue</h1>

    <p class="subtitle">
        The application below is requesting access to your account.
    </p>

    <div class="app-badge">
        <span>🖥</span>
        <span>{{ client_name }}</span>
    </div>

    <div class="scope-box">
        <p>Permissions requested</p>

        {% for s in scope.split() %}
            <span class="scope-tag">{{ s }}</span>
        {% endfor %}
    </div>

    {% if error %}
        <div class="error-msg">
            ⚠ {{ error }}
        </div>
    {% endif %}

    <form method="POST" action="/login">

        <label for="username">Username</label>

        <input
            id="username"
            name="username"
            type="text"
            placeholder="e.g. alice"
            autocomplete="username"
            required
        >

        <label for="password">Password</label>

        <input
            id="password"
            name="password"
            type="password"
            placeholder="Enter your password"
            autocomplete="current-password"
            required
        >

        <button class="btn" type="submit">
            Sign In
        </button>

    </form>

    <div class="hint">
        <strong>Demo accounts:</strong><br>
        alice / pass123 &nbsp;·&nbsp;
        bob / letmein &nbsp;·&nbsp;
        rohith / rohith99
    </div>

    <div class="divider"></div>

    <div class="server-badge">
        OAuth2 Authorization Server — Simulation Lab
    </div>

</div>

</body>
</html>
"""

# ============================================================
# CONSENT PAGE
# ============================================================

CONSENT_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>OAuth2 Consent</title>
    <style>{{ css|safe }}</style>
</head>

<body>

<div class="card">

    <div class="lock-icon">🔐</div>

    <h1>Authorize application</h1>

    <p class="subtitle">
        Review the permissions requested by this application.
    </p>

    <div class="app-badge">
        <span>🖥</span>
        <span>{{ client_name }}</span>
    </div>

    <div class="scope-box">

        <p>Permissions requested</p>

        {% for s in scope.split() %}

            <div style="
                display:flex;
                align-items:center;
                gap:10px;
                padding:10px 0;
            ">

                <div style="font-size:20px;">🔑</div>

                <div style="flex:1;">
                    <strong>{{ s }}</strong>
                    <div style="
                        color:#94a3b8;
                        font-size:12px;
                        margin-top:3px;
                    ">
                        OAuth permission
                    </div>
                </div>

                <span style="color:#10b981;font-size:12px;">
                    ✓
                </span>

            </div>

        {% endfor %}

    </div>

    <div class="hint">

        <strong>Signed in as:</strong>
        {{ username }}

    </div>

    <div class="error-msg"
         style="
         background:rgba(245,158,11,.1);
         border-color:rgba(245,158,11,.3);
         color:#fcd34d;
         margin-top:18px;
         ">

        ⚠ By approving,
        <strong>{{ client_name }}</strong>
        will be able to access the listed information using
        an access token. You can revoke this at any time.

    </div>

    <div class="btn-row">

        <form method="POST"
              action="/consent"
              style="flex:1">

            <input type="hidden"
                   name="decision"
                   value="deny">

            <button
                class="btn btn-deny"
                type="submit">

                Deny

            </button>

        </form>

        <form method="POST"
              action="/consent"
              style="flex:1">

            <input type="hidden"
                   name="decision"
                   value="approve">

            <button
                class="btn btn-approve"
                type="submit">

                ✓ Approve

            </button>

        </form>

    </div>

    <div class="divider"></div>

    <div class="server-badge">
        OAuth2 Authorization Server — Simulation Lab
    </div>

</div>

</body>
</html>
"""

# ============================================================
# AUTHORIZATION ENDPOINT
# ============================================================

@app.route("/authorize", methods=["GET"])
def authorize():

    client_id = request.args.get("client_id")
    redirect_uri = request.args.get("redirect_uri")
    response_type = request.args.get("response_type")
    scope = request.args.get("scope", "")
    state = request.args.get("state")

    client = store.CLIENTS.get(client_id)

    if not client:
        return "Unknown client_id", 400

    if response_type != "code":
        return "Unsupported response_type", 400

    if redirect_uri not in client["redirect_uris"]:
        return "Invalid redirect_uri", 400

    requested_scopes = scope.split()

    for s in requested_scopes:
        if s not in client["allowed_scopes"]:
            return f"Invalid scope: {s}", 400

    # Save OAuth transaction temporarily in session
    session["oauth_request"] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state
    }

    # If user isn't logged in, send to login
    if "username" not in session:
        return redirect(
            "/login?client_id=" +
            client_id +
            "&scope=" +
            scope
        )

    return render_template_string(
        CONSENT_HTML,
        css=BASE_CSS,
        client_name=client["name"],
        username=session["username"],
        scope=scope
    )


# ============================================================
# LOGIN GET
# ============================================================

@app.route("/login", methods=["GET"])
def login_page():

    client_id = request.args.get("client_id")
    scope = request.args.get("scope", "")

    if not client_id:
        oauth_request = session.get("oauth_request", {})
        client_id = oauth_request.get("client_id")

    client = store.CLIENTS.get(client_id)

    if not client:
        return "Invalid client", 400

    return render_template_string(
        LOGIN_HTML,
        css=BASE_CSS,
        client_name=client["name"],
        scope=scope,
        error=None
    )


# ============================================================
# LOGIN POST
# ============================================================

@app.route("/login", methods=["POST"])
def login():

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    user = store.USERS.get(username)

    if not user or user["password"] != password:

        oauth_request = session.get("oauth_request", {})
        client = store.CLIENTS.get(
            oauth_request.get("client_id")
        )

        return render_template_string(
            LOGIN_HTML,
            css=BASE_CSS,
            client_name=client["name"] if client else "OAuth Client",
            scope=oauth_request.get("scope", ""),
            error="Invalid username or password."
        ), 401

    session["username"] = username

    oauth_request = session.get("oauth_request")

    if not oauth_request:
        return "OAuth transaction expired. Start again.", 400

    client = store.CLIENTS.get(
        oauth_request["client_id"]
    )

    return render_template_string(
        CONSENT_HTML,
        css=BASE_CSS,
        client_name=client["name"],
        username=username,
        scope=oauth_request["scope"]
    )


# ============================================================
# CONSENT ENDPOINT
# ============================================================

@app.route("/consent", methods=["POST"])
def consent():

    decision = request.form.get("decision")

    oauth_request = session.get("oauth_request")

    if not oauth_request:
        return "OAuth transaction expired.", 400

    if decision == "deny":

        redirect_uri = oauth_request["redirect_uri"]
        state = oauth_request.get("state")

        params = {
            "error": "access_denied"
        }

        if state:
            params["state"] = state

        session.pop("oauth_request", None)

        return redirect(
            redirect_uri + "?" + urlencode(params)
        )

    if decision != "approve":
        return "Invalid decision", 400

    username = session.get("username")

    if not username:
        return "User is not authenticated.", 401

    client_id = oauth_request["client_id"]

    # Generate authorization code
    code = store.generate_token()

    store.AUTH_CODES[code] = {
        "client_id": client_id,
        "redirect_uri": oauth_request["redirect_uri"],
        "scope": oauth_request["scope"],
        "user": username,
        "used": False,
        "expires_at": time.time() + AUTH_CODE_TTL
    }

    redirect_uri = oauth_request["redirect_uri"]

    params = {
        "code": code
    }

    # Bind response to original state
    if oauth_request.get("state"):
        params["state"] = oauth_request["state"]

    session.pop("oauth_request", None)

    return redirect(
        redirect_uri + "?" + urlencode(params)
    )


# ============================================================
# TOKEN ENDPOINT
# ============================================================

@app.route("/oauth/token", methods=["POST"])
def token():

    grant_type = request.form.get(
        "grant_type"
    )

    code = request.form.get("code")
    client_id = request.form.get("client_id")
    client_secret = request.form.get("client_secret")
    redirect_uri = request.form.get("redirect_uri")

    # Check grant type
    if grant_type != "authorization_code":
        return jsonify({
            "error": "unsupported_grant_type"
        }), 400

    # Authenticate client
    client = store.CLIENTS.get(client_id)

    if not client:
        return jsonify({
            "error": "invalid_client"
        }), 401

    if not secrets.compare_digest(
        client_secret or "",
        client["client_secret"]
    ):
        return jsonify({
            "error": "invalid_client"
        }), 401

    # Check authorization code
    code_data = store.AUTH_CODES.get(code)

    if not code_data:
        return jsonify({
            "error": "invalid_grant",
            "error_description": "Unknown authorization code"
        }), 400

    # Single-use enforcement
    if code_data["used"]:
        return jsonify({
            "error": "invalid_grant",
            "error_description": "Authorization code already used"
        }), 400

    # Expiration
    if time.time() > code_data["expires_at"]:
        return jsonify({
            "error": "invalid_grant",
            "error_description": "Authorization code expired"
        }), 400

    # Bind code to client
    if code_data["client_id"] != client_id:
        return jsonify({
            "error": "invalid_grant",
            "error_description": "Code was not issued to this client"
        }), 400

    # Bind code to redirect URI
    if redirect_uri != code_data["redirect_uri"]:
        return jsonify({
            "error": "invalid_grant",
            "error_description": "Redirect URI mismatch"
        }), 400

    # Mark code as used
    store.AUTH_CODES[code]["used"] = True

    # Issue access token
    access_token = store.generate_token()

    store.store_access_token(
        token=access_token,
        client_id=client_id,
        scope=code_data["scope"],
        user=code_data["user"]
    )

    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": TOKEN_TTL,
        "scope": code_data["scope"]
    })


# ============================================================
# CLIENT INFO
# ============================================================

@app.route("/client/info", methods=["GET"])
def client_info():

    """Return registered client info for the lab UI."""

    c = list(store.CLIENTS.values())[0]

    return jsonify({
        "client_id": c["client_id"],
        "client_secret": c["client_secret"],
        "name": c["name"],
        "allowed_scopes": c["allowed_scopes"],
        "redirect_uris": c["redirect_uris"]
    })


# ============================================================
# CLIENT INSPECTOR
# ============================================================

@app.route("/client/inspect", methods=["GET"])
def client_inspect():

    """Live snapshot of in-memory codes and tokens."""

    now = time.time()

    codes = []

    for code, data in store.AUTH_CODES.items():

        codes.append({
            "preview": code[:16] + "…",
            "user": data["user"],
            "scope": data["scope"],
            "used": data["used"],
            "expired": now > data["expires_at"],
            "ttl": max(
                0,
                int(data["expires_at"] - now)
            )
        })

    tokens = []

    for token, data in store.ACCESS_TOKENS.items():

        tokens.append({
            "preview": token[:16] + "…",
            "user": data["user"],
            "scope": data["scope"],
            "expired": now > data["expires_at"],
            "ttl": max(
                0,
                int(data["expires_at"] - now)
            )
        })

    return jsonify({
        "codes": codes,
        "tokens": tokens,
        "users": list(store.USERS.keys()),
        "now": int(now)
    })


# ============================================================
# CALLBACK
# ============================================================

@app.route("/callback", methods=["GET"])
def callback():

    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    if error:
        return f"""
        <html>
        <head>
            <title>OAuth Error</title>
            <style>{BASE_CSS}</style>
        </head>
        <body>
            <div class="card">
                <div class="lock-icon">❌</div>
                <h1>Authorization Failed</h1>
                <p class="subtitle">
                    Error: {error}
                </p>
                <a href="/lab">
                    <button class="btn">Back to Lab</button>
                </a>
            </div>
        </body>
        </html>
        """

    if not code:
        return "No authorization code received.", 400

    # In a real OAuth client, the state would be compared
    # against the state originally generated by the client.
    state_status = "Received" if state else "Missing"

    return f"""
    <html>
    <head>
        <title>OAuth Callback</title>
        <style>{BASE_CSS}</style>
    </head>

    <body>

    <div class="card">

        <div class="lock-icon">✅</div>

        <h1>Authorization Code Received</h1>

        <p class="subtitle">
            The client successfully received an authorization code.
        </p>

        <div class="info-row">
            <span>Authorization Code</span>
            <span>{code[:16]}…</span>
        </div>

        <div class="info-row">
            <span>State</span>
            <span>{state_status}</span>
        </div>

        <div class="hint">
            The next step is exchanging this authorization code
            for an access token at <strong>/oauth/token</strong>.
        </div>

        <a href="/lab">
            <button class="btn">
                Return to Virtual Lab
            </button>
        </a>

    </div>

    </body>
    </html>
    """


# ============================================================
# LAB DASHBOARD
# ============================================================

LAB_HTML = """
<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>OAuth2 Virtual Lab</title>

    <style>
        {{ css|safe }}
    </style>

</head>

<body>

<header class="container">

    <h1>OAuth2 Authentication Lab</h1>

    <p>
        Authorization Code Grant — Basic Flow Simulation
    </p>

    <div class="status" id="serverStatus">

        <span class="status-dot"></span>

        <span>Checking server...</span>

    </div>

</header>


<main class="container">

    <section class="workflow">

        <div class="step active">
            <div class="step-number">1</div>
            Client
        </div>

        <div class="step">
            <div class="step-number">2</div>
            Login
        </div>

        <div class="step">
            <div class="step-number">3</div>
            Consent
        </div>

        <div class="step">
            <div class="step-number">4</div>
            Code
        </div>

        <div class="step">
            <div class="step-number">5</div>
            Token
        </div>

    </section>


    <section class="grid">

        <div class="panel">

            <h2>Registered Client</h2>

            <div id="clientInfo">
                Loading...
            </div>

        </div>


        <div class="panel">

            <h2>Start OAuth Flow</h2>

            <p>
                Start the Authorization Code Grant simulation.
                You will be asked to sign in and approve the
                requested permissions.
            </p>

            <button
                class="btn"
                onclick="startOAuth()">

                Start Authorization

            </button>

        </div>


        <div class="panel">

            <h2>Security Tests</h2>

            <p>
                Demonstration checks for common OAuth security
                properties.
            </p>

            <button
                class="security-test"
                type="button"
                data-challenge="state">

                state round-trip

            </button>

            <button
                class="security-test"
                type="button"
                data-challenge="code">

                single-use code

            </button>

            <button
                class="security-test"
                type="button"
                data-challenge="ttl">

                code TTL

            </button>

            <button
                class="security-test"
                type="button"
                data-challenge="client">

                client authentication

            </button>

        </div>


        <div class="panel">

            <h2>Authorization Codes</h2>

            <div id="codes">
                Loading...
            </div>

        </div>


        <div class="panel">

            <h2>Access Tokens</h2>

            <div id="tokens">
                Loading...
            </div>

        </div>


        <div class="panel">

            <h2>Lab Explanation</h2>

            <p>
                OAuth is not encryption of the user's password.
                It is an authorization protocol that allows a
                client application to obtain limited access on
                behalf of a resource owner.
            </p>

            <p>
                This simulation demonstrates authorization codes,
                consent, state, client authentication, expiration,
                single-use enforcement and bearer access tokens.
            </p>

        </div>

    </section>

</main>


<footer class="lab-footer">

    <span>
        BCS703 · Group 29 · Rohith · Nishith R Poojary
    </span>

    <span>
        Virtual lab · Authorization Code Grant
    </span>

</footer>


<div
    class="toast"
    id="toast"
    role="status"
    aria-live="polite">
</div>


<script>

async function loadClientInfo() {

    try {

        const response =
            await fetch("/client/info");

        const data =
            await response.json();

        document.getElementById("clientInfo").innerHTML = `

            <div class="info-row">
                <span>Name</span>
                <span>${data.name}</span>
            </div>

            <div class="info-row">
                <span>Client ID</span>
                <span>${data.client_id}</span>
            </div>

            <div class="info-row">
                <span>Scopes</span>
                <span>${data.allowed_scopes.join(", ")}</span>
            </div>

            <div class="info-row">
                <span>Redirect URI</span>
                <span>${data.redirect_uris[0]}</span>
            </div>

        `;

    } catch {

        document.getElementById("clientInfo").textContent =
            "Unable to load client information.";

    }
}


async function refreshStore() {

    try {

        const response =
            await fetch("/client/inspect");

        const data =
            await response.json();

        const codes =
            document.getElementById("codes");

        const tokens =
            document.getElementById("tokens");


        if (!data.codes.length) {

            codes.innerHTML =
                "<p>No authorization codes yet.</p>";

        } else {

            codes.innerHTML = `

                <table>

                    <tr>
                        <th>Code</th>
                        <th>User</th>
                        <th>Used</th>
                        <th>TTL</th>
                    </tr>

                    ${data.codes.map(c => `

                        <tr>

                            <td>${c.preview}</td>

                            <td>${c.user}</td>

                            <td>
                                <span class="badge ${
                                    c.used ? "good" : "bad"
                                }">
                                    ${c.used ? "Used" : "Unused"}
                                </span>
                            </td>

                            <td>
                                ${c.expired
                                    ? "Expired"
                                    : c.ttl + "s"}
                            </td>

                        </tr>

                    `).join("")}

                </table>

            `;

        }


        if (!data.tokens.length) {

            tokens.innerHTML =
                "<p>No access tokens yet.</p>";

        } else {

            tokens.innerHTML = `

                <table>

                    <tr>
                        <th>Token</th>
                        <th>User</th>
                        <th>TTL</th>
                    </tr>

                    ${data.tokens.map(t => `

                        <tr>

                            <td>${t.preview}</td>

                            <td>${t.user}</td>

                            <td>
                                ${t.expired
                                    ? "Expired"
                                    : t.ttl + "s"}
                            </td>

                        </tr>

                    `).join("")}

                </table>

            `;

        }

    } catch {

        document.getElementById("codes").textContent =
            "Server unavailable.";

        document.getElementById("tokens").textContent =
            "Server unavailable.";

    }
}


async function checkServer() {

    try {

        const response =
            await fetch("/client/inspect");

        const statusText =
            document
                .getElementById("serverStatus")
                .querySelector("span:last-child");

        const status =
            document.getElementById("serverStatus");

        status.classList.toggle(
            "online",
            response.ok
        );

        statusText.textContent =
            response.ok
                ? "Server online"
                : "Server unavailable";

    } catch {

        const status =
            document.getElementById("serverStatus");

        status.classList.remove("online");

        status.querySelector(
            "span:last-child"
        ).textContent = "Server unavailable";

    }

}


function startOAuth() {

    const state =
        crypto.randomUUID();

    sessionStorage.setItem(
        "oauth_state",
        state
    );

    const params =
        new URLSearchParams({

            client_id: "{{ client_id }}",

            redirect_uri:
                "http://127.0.0.1:5000/callback",

            response_type: "code",

            scope:
                "profile email read",

            state: state

        });

    window.location.href =
        "/authorize?" + params.toString();

}


function setActiveStep(step) {

    const steps =
        document.querySelectorAll(".step");

    steps.forEach((element, index) => {

        element.classList.toggle(
            "active",
            index === step
        );

    });

}


document.querySelectorAll(
    ".security-test"
).forEach(button => {

    button.addEventListener(
        "click",
        () => {

            const challenge =
                button.dataset.challenge;

            let message = "";

            if (challenge === "state") {

                message =
                    "State protects the authorization request from CSRF-style response injection.";

            }

            else if (challenge === "code") {

                message =
                    "Authorization codes are marked used after token exchange and cannot be exchanged again.";

            }

            else if (challenge === "ttl") {

                message =
                    "Authorization codes expire after a short TTL.";

            }

            else if (challenge === "client") {

                message =
                    "The token endpoint authenticates the registered client before issuing a token.";

            }

            showToast(message);

        }
    );

});


function showToast(message) {

    const toast =
        document.getElementById("toast");

    toast.textContent = message;

    toast.classList.add("show");

    setTimeout(() => {

        toast.classList.remove("show");

    }, 3500);

}


loadClientInfo();
checkServer();

setInterval(
    checkServer,
    10000
);

setInterval(
    refreshStore,
    2500
);

refreshStore();

setActiveStep(0);

</script>

</body>
</html>
"""


# ============================================================
# LAB ROUTE
# ============================================================

@app.route("/", methods=["GET"])
@app.route("/lab", methods=["GET"])
def lab():

    return render_template_string(
        LAB_HTML,
        css=BASE_CSS,
        client_id=CLIENT_ID
    )


# ============================================================
# SIMPLE PROTECTED RESOURCE
# ============================================================

@app.route("/api/profile", methods=["GET"])
def profile():

    auth_header = request.headers.get(
        "Authorization", ""
    )

    if not auth_header.startswith("Bearer "):

        return jsonify({
            "error": "missing_bearer_token"
        }), 401

    token = auth_header.split(
        " ",
        1
    )[1]

    data = store.ACCESS_TOKENS.get(token)

    if not data:

        return jsonify({
            "error": "invalid_token"
        }), 401

    if time.time() > data["expires_at"]:

        return jsonify({
            "error": "expired_token"
        }), 401

    return jsonify({
        "user": data["user"],
        "name": store.USERS[data["user"]]["name"],
        "email": store.USERS[data["user"]]["email"],
        "scope": data["scope"]
    })


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("OAuth2 Authorization Server — Simulation Lab")
    print("=" * 60)
    print()
    print("Client ID     :", CLIENT_ID)
    print("Client Secret :", CLIENT_SECRET)
    print()
    print("Demo Users:")
    print("  alice  / pass123")
    print("  bob    / letmein")
    print("  rohith / rohith99")
    print()
    print("Lab URL:")
    print("  http://127.0.0.1:5000/lab")
    print()
    print("Authorization endpoint:")
    print("  http://127.0.0.1:5000/authorize")
    print()
    print("Token endpoint:")
    print("  http://127.0.0.1:5000/oauth/token")
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
