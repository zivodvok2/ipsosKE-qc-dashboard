import bcrypt
import streamlit as st
import database as db
from config import ROLES


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def login(email: str, password: str):
    user = db.get_user_by_email(email.strip().lower())
    if not user:
        return False, "Invalid email or password."
    if not verify_password(password, user["password_hash"]):
        return False, "Invalid email or password."
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = user["id"]
    st.session_state["user_email"] = user["email"]
    st.session_state["user_name"] = user["full_name"]
    st.session_state["user_role"] = user["role"]
    st.session_state["page"] = "dashboard"
    st.session_state["project_id"] = None
    st.session_state["project_tab"] = "quality_report"
    return True, None


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def guest_login():
    st.session_state["logged_in"] = True
    st.session_state["user_id"] = None
    st.session_state["user_email"] = None
    st.session_state["user_name"] = "Guest"
    st.session_state["user_role"] = "qc_executive"
    st.session_state["is_guest"] = True
    st.session_state["page"] = "dashboard"
    st.session_state["project_id"] = None
    st.session_state["project_tab"] = "quality_report"


def require_login():
    return st.session_state.get("logged_in", False)


def require_role(*roles):
    return st.session_state.get("user_role") in roles


def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """<div style="text-align:center; padding: 2rem 0 1rem 0;">
                <h1 style="color:#1F2B6C; font-size:2.2rem; font-weight:800;">IpsosKE</h1>
                <h3 style="color:#00B5AD; margin-top:-0.5rem;">QC Dashboard</h3>
               </div>""",
            unsafe_allow_html=True,
        )

        tab_login, tab_register = st.tabs(["Sign In", "Register"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                ok, err = login(email, password)
                if ok:
                    st.rerun()
                else:
                    st.error(err)

        with tab_register:
            with st.form("register_form"):
                r_name = st.text_input("Full Name")
                r_email = st.text_input("Email", placeholder="your@email.com")
                r_pass = st.text_input("Password", type="password")
                r_pass2 = st.text_input("Confirm Password", type="password")
                submitted2 = st.form_submit_button("Create Account", use_container_width=True)
            if submitted2:
                if not r_name or not r_email or not r_pass:
                    st.error("All fields are required.")
                elif r_pass != r_pass2:
                    st.error("Passwords do not match.")
                elif len(r_pass) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    ok, err = db.create_user(
                        r_email.strip().lower(),
                        hash_password(r_pass),
                        r_name.strip(),
                        "other",
                    )
                    if ok:
                        st.success("Account created. You can now sign in. Your role will be set by an admin.")
                    else:
                        st.error(err)

        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; color:#888; font-size:0.85rem;'>Prototype mode — no account required</p>",
            unsafe_allow_html=True,
        )
        if st.button("Continue as Guest", use_container_width=True, type="secondary"):
            guest_login()
            st.rerun()
