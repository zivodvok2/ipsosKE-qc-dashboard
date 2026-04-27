import streamlit as st
import database as db
from auth import show_login_page, logout, require_login
from config import ROLES, ADMIN_ROLES, IPSOS_NAVY, IPSOS_TEAL

st.set_page_config(
    page_title="IpsosKE QC Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialise DB once per session
if "db_init" not in st.session_state:
    db.init_db()
    st.session_state["db_init"] = True

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #1F2B6C;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] .stButton button {
    background: transparent;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 6px;
    width: 100%;
    text-align: left;
    padding: 0.5rem 0.8rem;
    margin: 2px 0;
    font-size: 0.9rem;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(0, 181, 173, 0.3) !important;
    border-color: #00B5AD !important;
}
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
    color: #1F2B6C;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #00B5AD;
}
div[data-testid="metric-container"] {
    background: white;
    border-radius: 8px;
    padding: 0.8rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.07);
}
</style>
""", unsafe_allow_html=True)


def _nav_button(label, page_key, icon=""):
    current = st.session_state.get("page", "dashboard")
    active_style = "border-left: 3px solid #00B5AD !important;" if current == page_key else ""
    clicked = st.button(f"{icon} {label}", key=f"nav_{page_key}")
    if clicked:
        st.session_state["page"] = page_key
        if page_key == "dashboard":
            st.session_state["project_id"] = None
        st.rerun()


def _sidebar():
    with st.sidebar:
        st.markdown(
            """<div style="text-align:center; padding: 1rem 0 1.5rem 0;">
                <div style="font-size:1.8rem; font-weight:800; color:white;">IpsosKE</div>
                <div style="color:#00B5AD; font-size:0.9rem;">QC Dashboard</div>
            </div>""",
            unsafe_allow_html=True,
        )

        role = st.session_state.get("user_role", "other")
        name = st.session_state.get("user_name", "")
        is_guest = st.session_state.get("is_guest", False)

        guest_badge = (
            " <span style='background:#D4E157; color:#1F2B6C; font-size:0.7rem; "
            "padding:1px 6px; border-radius:4px; font-weight:700;'>GUEST</span>"
            if is_guest else ""
        )
        st.markdown(
            f"""<div style="background:rgba(255,255,255,0.1); border-radius:8px;
                 padding:0.6rem 0.8rem; margin-bottom:1rem; font-size:0.85rem;">
                <div style="font-weight:600;">{name}{guest_badge}</div>
                <div style="color:#00B5AD;">{ROLES.get(role, role)}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("**Navigation**")
        _nav_button("Dashboard", "dashboard", "🏠")

        if role in ADMIN_ROLES:
            _nav_button("Admin Panel", "admin", "⚙️")

        st.markdown("---")
        sign_out_label = "🚪 Exit Guest" if is_guest else "🚪 Sign Out"
        if st.button(sign_out_label, key="nav_logout"):
            logout()
            st.rerun()

        st.markdown(
            """<div style="position:fixed; bottom:1rem; left:1rem; right:1rem;
                 font-size:0.7rem; color:rgba(255,255,255,0.4); text-align:center;">
                © Ipsos 2025 | QC Dashboard | Internal Use
            </div>""",
            unsafe_allow_html=True,
        )


def _route():
    page = st.session_state.get("page", "dashboard")

    if page == "dashboard":
        from pages_modules import dashboard
        dashboard.show()

    elif page == "project_detail":
        from pages_modules import project_detail
        project_detail.show()

    elif page == "admin":
        from pages_modules import admin
        admin.show()

    else:
        from pages_modules import dashboard
        dashboard.show()


def main():
    if not require_login():
        show_login_page()
        return

    _sidebar()

    with st.container():
        _route()


if __name__ == "__main__":
    main()
else:
    main()
