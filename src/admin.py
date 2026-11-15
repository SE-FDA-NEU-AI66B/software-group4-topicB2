"""US12 management API. Actor identity always comes from the authenticated session."""

from flask import Blueprint, jsonify, request, session

AREA_DENIED = "You do not have permission to access this area."
SUPPORT_DEFAULT = "Contact your university administrator if you need access."
SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY CHECK (key = 'support_contact'),
    value TEXT NOT NULL CHECK (length(trim(value)) BETWEEN 1 AND 200),
    updated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_at TEXT NOT NULL
)
"""


def support_setting(connection):
    # Old deployments can render the existing login help before migration.
    if connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='system_settings'").fetchone():
        row = connection.execute("SELECT value, updated_at FROM system_settings WHERE key=?", ("support_contact",)).fetchone()
        if row:
            return {"key": "support_contact", "value": row["value"], "updated_at": row["updated_at"]}
    return {"key": "support_contact", "value": SUPPORT_DEFAULT, "updated_at": None}


def register_admin(app, connect, login_required, api_error, valid_roles, clock):
    blueprint = Blueprint("admin", __name__, url_prefix="/api/admin")
    required = login_required(roles=["administrator"], forbidden_message=AREA_DENIED)

    def actor_allowed(connection):
        actor = connection.execute("SELECT role FROM users WHERE id=?", (session["user_id"],)).fetchone()
        return actor is not None and actor["role"] == "administrator"

    def forbidden():
        return api_error(403, "FORBIDDEN", AREA_DENIED, "Sign in with an administrator account.")

    @blueprint.get("")
    @required
    def management():
        return jsonify({"users_url": "/api/admin/users", "settings_url": "/api/admin/settings"})

    @blueprint.get("/users")
    @required
    def users():
        with connect() as db:
            if not actor_allowed(db):
                return forbidden()
            rows = db.execute("SELECT id, email, full_name, role FROM users ORDER BY id").fetchall()
        return jsonify({"users": [dict(row) for row in rows]})

    @blueprint.patch("/users/<int:user_id>/role")
    @required
    def update_role(user_id):
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {"role"}:
            return api_error(400, "INVALID_REQUEST", "Send exactly one role field.", "Use a JSON object with role.")
        role = data["role"]
        if not isinstance(role, str) or role not in valid_roles:
            return api_error(400, "INVALID_ROLE", "Role must be student, lecturer, or administrator.", "Choose a supported role.")
        with connect() as db:
            # Serialize authorization and write with other role changes.
            db.execute("BEGIN IMMEDIATE")
            if not actor_allowed(db):
                return forbidden()
            cursor = db.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
            if cursor.rowcount != 1:
                return api_error(404, "USER_NOT_FOUND", "The user does not exist.", "Refresh the user list.")
        return jsonify({"user": {"id": user_id, "role": role}})

    @blueprint.get("/settings")
    @required
    def settings():
        with connect() as db:
            if not actor_allowed(db):
                return forbidden()
            setting = support_setting(db)
        return jsonify({"settings": [{**setting, "type": "string", "min_length": 1, "max_length": 200}]})

    @blueprint.put("/settings/<key>")
    @required
    def update_setting(key):
        if key != "support_contact":
            return api_error(400, "UNSUPPORTED_SETTING", "This setting is not supported.", "Use a key returned by GET /api/admin/settings.")
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) != {"value"}:
            return api_error(400, "INVALID_REQUEST", "Send exactly one value field.", "Use a JSON object with value.")
        value = data["value"]
        if (not isinstance(value, str) or not 1 <= len(value.strip()) <= 200
                or any(ord(char) < 32 or ord(char) == 127 for char in value.strip())):
            return api_error(400, "INVALID_SETTING_VALUE", "Support contact must be 1 to 200 characters of plain text.", "Remove control characters and provide contact guidance.")
        value = value.strip()
        timestamp = clock()
        with connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if not actor_allowed(db):
                return forbidden()
            if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='system_settings'").fetchone():
                return api_error(503, "SETTINGS_NOT_INITIALIZED", "Settings storage is not initialized.", "Ask the operator to apply the US12 settings migration.")
            db.execute(
                "INSERT INTO system_settings (key,value,updated_by,updated_at) VALUES (?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_by=excluded.updated_by, updated_at=excluded.updated_at",
                (key, value, session["user_id"], timestamp),
            )
        return jsonify({"setting": {"key": key, "value": value, "updated_at": timestamp}})

    app.register_blueprint(blueprint)
