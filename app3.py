import secrets
import time
import os


# ============================================================
# OAuth2 Authorization Code Grant
# BCS703 Cryptography and Network Security
# Group 29 — Rohith, Nishith R Poojary
#
# TERMINAL-BASED VIRTUAL LAB
# ============================================================


# ============================================================
# CONFIGURATION
# ============================================================

CLIENT_ID = "lab-client-001"
CLIENT_SECRET = "lab-secret-123"

REDIRECT_URI = "http://127.0.0.1:5000/callback"

AUTH_CODE_TTL = 120
TOKEN_TTL = 3600


# ============================================================
# DEMO USERS
# ============================================================

USERS = {
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
# REGISTERED CLIENT
# ============================================================

CLIENT = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "name": "OAuth Virtual Lab Client",

    "allowed_scopes": [
        "profile",
        "email",
        "read"
    ],

    "redirect_uris": [
        REDIRECT_URI
    ]
}


# ============================================================
# IN-MEMORY STORAGE
# ============================================================

AUTH_CODES = {}
ACCESS_TOKENS = {}


# ============================================================
# TERMINAL COLORS
# ============================================================

RESET = "\033[0m"
BOLD = "\033[1m"

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"


# ============================================================
# TERMINAL FUNCTIONS
# ============================================================

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def line(char="=", length=72):
    print(char * length)


def title(text):
    print()
    line("=")
    print(f"{BOLD}{CYAN}{text.center(72)}{RESET}")
    line("=")


def success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def error(text):
    print(f"{RED}✗ {text}{RESET}")


def warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")


def info(text):
    print(f"{BLUE}→ {text}{RESET}")


def pause():
    input(f"\n{YELLOW}Press ENTER to continue...{RESET}")


# ============================================================
# SECURE TOKEN GENERATION
# ============================================================

def generate_secure_token(length=32):
    return secrets.token_urlsafe(length)


# ============================================================
# STEP 1 — CLIENT REGISTRATION
# ============================================================

def step_1_client():

    clear()

    title("STEP 1 — CLIENT REGISTRATION")

    print()
    print(f"{BOLD}OAuth Client Information{RESET}")
    line("-")

    print(f"Client Name       : {CLIENT['name']}")
    print(f"Client ID         : {CLIENT['client_id']}")
    print(f"Client Secret     : {CLIENT['client_secret']}")

    print(
        "Allowed Scopes    : "
        + ", ".join(CLIENT["allowed_scopes"])
    )

    print(
        "Redirect URI      : "
        + CLIENT["redirect_uris"][0]
    )

    print()

    success("Client is registered with the Authorization Server.")

    print()
    info("The client ID identifies the application.")
    info("The client secret authenticates the confidential client.")
    info("The redirect URI identifies the callback destination.")
    info("Scopes define the permissions requested by the client.")

    pause()


# ============================================================
# STEP 2 — USER LOGIN
# ============================================================

def step_2_login():

    clear()

    title("STEP 2 — USER LOGIN")

    print()
    print(f"{BOLD}OAuth Authorization Server{RESET}")
    print("The client is requesting access to the user's account.")
    print()

    print("Demo Accounts")
    line("-")

    for username, data in USERS.items():
        print(
            f"  {username:<10} / "
            f"{data['password']}"
        )

    print()

    while True:

        username = input(
            f"{CYAN}Username: {RESET}"
        ).strip()

        password = input(
            f"{CYAN}Password: {RESET}"
        ).strip()

        if username not in USERS:

            error("Unknown username.")
            continue

        if USERS[username]["password"] != password:

            error("Incorrect password.")
            continue

        success(
            f"User '{username}' authenticated successfully."
        )

        return username


# ============================================================
# STEP 3 — USER CONSENT
# ============================================================

def step_3_consent(username):

    clear()

    title("STEP 3 — USER CONSENT")

    print()
    print(
        f"{BOLD}{CLIENT['name']}{RESET}"
    )

    print()
    print(
        f"User: {GREEN}{username}{RESET}"
    )

    print()
    print("Permissions requested:")
    line("-")

    scopes = [
        "profile",
        "email",
        "read"
    ]

    for scope in scopes:

        if scope == "profile":
            description = "Access basic profile information"

        elif scope == "email":
            description = "Access user's email address"

        else:
            description = "Read permitted protected information"

        print(
            f"  🔑 {scope:<10} - {description}"
        )

    print()

    warning(
        "By approving, the client will be able to use "
        "an access token for the listed permissions."
    )

    print()

    while True:

        decision = input(
            "Approve access? [Y/N]: "
        ).strip().lower()

        if decision in ["y", "yes"]:

            success(
                "User approved the requested permissions."
            )

            return True

        if decision in ["n", "no"]:

            error(
                "User denied the requested permissions."
            )

            return False

        warning("Please enter Y or N.")


# ============================================================
# STATE GENERATION
# ============================================================

def generate_state():

    return secrets.token_urlsafe(24)


# ============================================================
# STEP 4 — AUTHORIZATION CODE
# ============================================================

def step_4_authorization_code(username):

    clear()

    title("STEP 4 — AUTHORIZATION CODE")

    state = generate_state()

    print()
    info("Generating secure state parameter...")

    print(
        f"State: {MAGENTA}{state}{RESET}"
    )

    print()

    # --------------------------------------------------------
    # STATE ROUND-TRIP
    # --------------------------------------------------------

    print(
        f"{BOLD}State Round-Trip Verification{RESET}"
    )

    line("-")

    returned_state = state

    if returned_state == state:

        success(
            "State verification successful."
        )

    else:

        error(
            "State verification failed."
        )

        return None

    print()

    # --------------------------------------------------------
    # AUTHORIZATION CODE
    # --------------------------------------------------------

    code = generate_secure_token(24)

    created = time.time()
    expires = created + AUTH_CODE_TTL

    AUTH_CODES[code] = {

        "client_id":
            CLIENT_ID,

        "redirect_uri":
            REDIRECT_URI,

        "scope":
            "profile email read",

        "user":
            username,

        "state":
            state,

        "created_at":
            created,

        "expires_at":
            expires,

        "used":
            False
    }

    print(
        f"{BOLD}Authorization Code Generated{RESET}"
    )

    line("-")

    print(
        f"Code Preview : "
        f"{GREEN}{code[:16]}...{RESET}"
    )

    print(
        f"User          : {username}"
    )

    print(
        "Scope         : profile email read"
    )

    print(
        f"TTL           : {AUTH_CODE_TTL} seconds"
    )

    print(
        "Used          : False"
    )

    print()

    success(
        "Authorization code created successfully."
    )

    info(
        "The authorization code is short-lived."
    )

    info(
        "The authorization code is single-use."
    )

    info(
        "The code is bound to the client and redirect URI."
    )

    pause()

    return code


# ============================================================
# CLIENT AUTHENTICATION
# ============================================================

def authenticate_client(client_id, client_secret):

    if client_id != CLIENT_ID:
        return False

    if client_secret != CLIENT_SECRET:
        return False

    return True


# ============================================================
# STEP 5 — TOKEN ENDPOINT
# ============================================================

def exchange_code_for_token(code):

    clear()

    title("STEP 5 — TOKEN EXCHANGE")

    print()

    print(
        f"{BOLD}POST /oauth/token{RESET}"
    )

    print()

    # --------------------------------------------------------
    # CLIENT AUTHENTICATION
    # --------------------------------------------------------

    print(
        f"{BOLD}1. Client Authentication{RESET}"
    )

    line("-")

    print(
        f"Client ID     : {CLIENT_ID}"
    )

    print(
        f"Client Secret : {CLIENT_SECRET}"
    )

    if not authenticate_client(
        CLIENT_ID,
        CLIENT_SECRET
    ):

        error(
            "Client authentication failed."
        )

        return None

    success(
        "Client authentication successful."
    )

    print()

    # --------------------------------------------------------
    # CODE VALIDATION
    # --------------------------------------------------------

    print(
        f"{BOLD}2. Authorization Code Validation{RESET}"
    )

    line("-")

    if code not in AUTH_CODES:

        error(
            "Authorization code does not exist."
        )

        return None

    code_data = AUTH_CODES[code]

    success(
        "Authorization code exists."
    )

    # --------------------------------------------------------
    # SINGLE USE CHECK
    # --------------------------------------------------------

    print()

    print(
        f"{BOLD}3. Single-Use Check{RESET}"
    )

    line("-")

    if code_data["used"]:

        error(
            "Authorization code has already been used."
        )

        return None

    success(
        "Authorization code has not been used."
    )

    # --------------------------------------------------------
    # TTL CHECK
    # --------------------------------------------------------

    print()

    print(
        f"{BOLD}4. TTL / Expiration Check{RESET}"
    )

    line("-")

    now = time.time()

    if now > code_data["expires_at"]:

        error(
            "Authorization code has expired."
        )

        return None

    remaining = int(
        code_data["expires_at"] - now
    )

    success(
        f"Authorization code is valid. "
        f"Remaining TTL: {remaining}s"
    )

    # --------------------------------------------------------
    # CLIENT BINDING
    # --------------------------------------------------------

    print()

    print(
        f"{BOLD}5. Client Binding Check{RESET}"
    )

    line("-")

    if code_data["client_id"] != CLIENT_ID:

        error(
            "Authorization code is not bound to this client."
        )

        return None

    success(
        "Authorization code is bound to the client."
    )

    # --------------------------------------------------------
    # REDIRECT URI VALIDATION
    # --------------------------------------------------------

    print()

    print(
        f"{BOLD}6. Redirect URI Validation{RESET}"
    )

    line("-")

    if code_data["redirect_uri"] != REDIRECT_URI:

        error(
            "Redirect URI validation failed."
        )

        return None

    success(
        "Redirect URI validation successful."
    )

    # --------------------------------------------------------
    # MARK CODE AS USED
    # --------------------------------------------------------

    print()

    print(
        f"{BOLD}7. Mark Authorization Code as Used{RESET}"
    )

    line("-")

    AUTH_CODES[code]["used"] = True

    success(
        "Authorization code marked as USED."
    )

    # --------------------------------------------------------
    # GENERATE ACCESS TOKEN
    # --------------------------------------------------------

    print()

    print(
        f"{BOLD}8. Generate Access Token{RESET}"
    )

    line("-")

    access_token = generate_secure_token(32)

    token_created = time.time()

    ACCESS_TOKENS[access_token] = {

        "client_id":
            CLIENT_ID,

        "scope":
            code_data["scope"],

        "user":
            code_data["user"],

        "created_at":
            token_created,

        "expires_at":
            token_created + TOKEN_TTL
    }

    success(
        "Access token generated."
    )

    print()

    print(
        f"{BOLD}OAuth2 Token Response{RESET}"
    )

    line("-")

    print("{")

    print(
        f'  "access_token": '
        f'"{access_token}",'
    )

    print(
        '  "token_type": "Bearer",'
    )

    print(
        f'  "expires_in": {TOKEN_TTL},'
    )

    print(
        f'  "scope": "{code_data["scope"]}"'
    )

    print("}")

    print()

    success(
        "Authorization Code Grant completed successfully."
    )

    return access_token


# ============================================================
# PROTECTED RESOURCE
# ============================================================

def protected_resource(access_token):

    clear()

    title("PROTECTED RESOURCE")

    print()

    print(
        f"{BOLD}GET /api/profile{RESET}"
    )

    print()

    if not access_token:

        error(
            "No access token supplied."
        )

        return

    if access_token not in ACCESS_TOKENS:

        error(
            "Invalid access token."
        )

        return

    token_data = ACCESS_TOKENS[access_token]

    if time.time() > token_data["expires_at"]:

        error(
            "Access token has expired."
        )

        return

    print(
        "Authorization Header:"
    )

    print(
        f"  Authorization: "
        f"Bearer {access_token[:18]}..."
    )

    print()

    success(
        "Access token accepted."
    )

    print()

    print(
        f"{BOLD}Protected Resource Response{RESET}"
    )

    line("-")

    user = token_data["user"]

    user_data = USERS[user]

    print("{")

    print(
        f'  "username": "{user}",'
    )

    print(
        f'  "name": "{user_data["name"]}",'
    )

    print(
        f'  "email": "{user_data["email"]}",'
    )

    print(
        f'  "scope": "{token_data["scope"]}"'
    )

    print("}")

    print()

    success(
        "Protected resource successfully accessed."
    )

    pause()


# ============================================================
# COMPLETE AUTOMATIC DEMONSTRATION
# ============================================================

def automatic_demo():

    clear()

    title(
        "COMPLETE OAUTH2 AUTHORIZATION CODE DEMONSTRATION"
    )

    print()

    print(
        "This demonstration executes the complete flow"
    )

    print(
        "directly inside the VS Code terminal."
    )

    print()

    pause()

    # STEP 1

    step_1_client()

    # STEP 2

    username = step_2_login()

    pause()

    # STEP 3

    approved = step_3_consent(username)

    if not approved:

        print()

        error(
            "OAuth authorization terminated by user."
        )

        pause()

        return

    pause()

    # STEP 4

    code = step_4_authorization_code(
        username
    )

    if not code:

        error(
            "Authorization code generation failed."
        )

        pause()

        return

    # STEP 5

    token = exchange_code_for_token(
        code
    )

    if not token:

        error(
            "Token exchange failed."
        )

        pause()

        return

    pause()

    # PROTECTED RESOURCE

    protected_resource(token)


# ============================================================
# MAIN MENU
# ============================================================

def main():

    while True:

        clear()

        title(
            "OAUTH2 AUTHORIZATION SERVER — SIMULATION LAB"
        )

        print()

        print(
            f"{GREEN}Server Status: ONLINE{RESET}"
        )

        print()

        print(
            f"{BOLD}Client ID:{RESET} "
            f"{CLIENT_ID}"
        )

        print(
            f"{BOLD}Redirect URI:{RESET} "
            f"{REDIRECT_URI}"
        )

        print()

        line("-")

        # ONLY OPTIONS 1–6 AND 0

        print(
            "1. Run Complete OAuth2 Flow"
        )

        print(
            "2. Step 1 — Client Registration"
        )

        print(
            "3. Step 2 — User Login"
        )

        print(
            "4. Step 3 — User Consent"
        )

        print(
            "5. Step 4 — Authorization Code"
        )

        print(
            "6. Step 5 — Access Token"
        )

        print(
            "0. Exit"
        )

        print()

        choice = input(
            f"{CYAN}Enter your choice: {RESET}"
        ).strip()

        # ----------------------------------------------------
        # OPTION 1
        # ----------------------------------------------------

        if choice == "1":

            automatic_demo()

        # ----------------------------------------------------
        # OPTION 2
        # ----------------------------------------------------

        elif choice == "2":

            step_1_client()

        # ----------------------------------------------------
        # OPTION 3
        # ----------------------------------------------------

        elif choice == "3":

            step_2_login()
            pause()

        # ----------------------------------------------------
        # OPTION 4
        # ----------------------------------------------------

        elif choice == "4":

            username = input(
                "Enter username: "
            ).strip()

            if username in USERS:

                step_3_consent(username)
                pause()

            else:

                error(
                    "Unknown user."
                )

                pause()

        # ----------------------------------------------------
        # OPTION 5
        # ----------------------------------------------------

        elif choice == "5":

            username = input(
                "Enter username: "
            ).strip()

            if username in USERS:

                step_4_authorization_code(
                    username
                )

            else:

                error(
                    "Unknown user."
                )

                pause()

        # ----------------------------------------------------
        # OPTION 6
        # ----------------------------------------------------

        elif choice == "6":

            if not AUTH_CODES:

                warning(
                    "No authorization code exists."
                )

                pause()

            else:

                code = list(
                    AUTH_CODES.keys()
                )[-1]

                exchange_code_for_token(
                    code
                )

                pause()

        # ----------------------------------------------------
        # OPTION 0
        # ----------------------------------------------------

        elif choice == "0":

            clear()

            print()

            line("=")

            print(
                f"{BOLD}{GREEN}"
                "OAuth2 Virtual Lab terminated."
                f"{RESET}"
            )

            print(
                "Thank you — Group 29"
            )

            line("=")

            print()

            break

        # ----------------------------------------------------
        # INVALID OPTION
        # ----------------------------------------------------

        else:

            warning(
                "Invalid option. Please try again."
            )

            time.sleep(1)


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":

    main()
