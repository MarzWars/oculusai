from functools import wraps
from flask import Blueprint, session, redirect, request, render_template
from backend.extensions import supabase
from backend.utils import _esc
auth_bp = Blueprint("auth", __name__)

def login_required(f):
    """Decorator — redirects to /login if the user is not in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

def current_user_id() -> str:
    return session.get("user_id", "")

def current_email() -> str:
    return session.get("email", "")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    error = ""
    success = ""

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        confirm = (request.form.get("confirm") or "").strip()

        if not email or not password:
            error = "Email and password are required."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                if res.user:
                    success = "Account created! You can now log in."
                else:
                    error = "Registration failed. Try a different email."
            except Exception as e:
                error = f"Registration error: {str(e)}"

    return render_template("register.html", error=error, success=success)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = ""

    if "user_id" in session:
        return redirect("/")

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()

        if not email or not password:
            error = "Email and password are required."
        else:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res.user:
                    uid = str(res.user.id)
                    session["user_id"] = uid
                    session["email"] = email
                    
                    # Ensure default workspace exists and initialize active workspace ID in session
                    from backend.workspaces import ensure_default_workspace
                    ensure_default_workspace(uid)
                    session["current_workspace_id"] = uid
                    
                    # Increment session count in memory
                    from backend.memory import load_memory, save_memory
                    mem = load_memory(uid, global_user_id=uid)
                    mem["session_count"] = mem.get("session_count", 0) + 1
                    save_memory(uid, mem, global_user_id=uid)
                    return redirect("/")
                else:
                    error = "Invalid email or password."
            except Exception:
                error = "Invalid email or password."

    return render_template("login.html", error=error)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    session.clear()
    return redirect("/login")
