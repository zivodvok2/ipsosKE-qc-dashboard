import streamlit as st
import database as db
from config import IPSOS_NAVY, IPSOS_TEAL, IPSOS_ORANGE
from pages_modules import (
    quality_report, backcheck_report, cancelled_interviews,
    performance_report, timing_report, listen_in, wave_comparison,
)


TABS = [
    ("Quality Report", "quality_report"),
    ("Back-check Report", "backcheck_report"),
    ("Cancelled Interviews", "cancelled_interviews"),
    ("Performance Report", "performance_report"),
    ("Timing Report", "timing_report"),
    ("Listen-in", "listen_in"),
    ("Wave Comparison", "wave_comparison"),
]


def show():
    project_id = st.session_state.get("project_id")
    if not project_id:
        st.error("No project selected.")
        return

    project = db.get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    # Check drill-down access
    user_id = st.session_state["user_id"]
    role = st.session_state["user_role"]
    if not db.user_can_drilldown(user_id, project_id, role):
        st.error("You do not have access to this project's details.")
        return

    # Back button
    if st.button("← Back to Dashboard"):
        st.session_state["page"] = "dashboard"
        st.session_state["project_id"] = None
        st.rerun()

    # Project header
    status_color = {"active": "#2E7D32", "completed": "#1565C0", "paused": "#E65100"}.get(
        project["status"], "#666"
    )

    # Compute live quota stats for the header
    qr_records = db.get_quality_records(project_id)
    approved_count = sum(1 for r in qr_records if str(r.get("approval_status", "")).lower() == "approved")
    target = project.get("sample_target") or 0
    overflow = approved_count - target
    overflow_str = f"+{overflow}" if overflow > 0 else str(overflow)
    overflow_color = "#D4E157" if overflow >= 0 else IPSOS_ORANGE

    bc_records = db.get_backcheck_records(project_id)
    bc_rate = round(len(bc_records) / approved_count * 100, 1) if approved_count else 0
    bc_target_pct = round((project.get("backcheck_target") or 0.20) * 100)
    li_records = db.get_listen_in_records(project_id)
    li_rate = round(len(li_records) / approved_count * 100, 1) if approved_count else 0
    li_target_pct = round((project.get("listenin_target") or 0.10) * 100)

    bc_icon = "✅" if bc_rate >= bc_target_pct else "⚠️"
    li_icon = "✅" if li_rate >= li_target_pct else "⚠️"

    st.markdown(
        f"""<div style="background:{IPSOS_NAVY}; color:white; padding:1.2rem 1.5rem;
             border-radius:10px; margin-bottom:1rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;">
                <div>
                    <h2 style="margin:0; color:white;">{project['name']}</h2>
                    <span style="color:#aaa;">Client: {project.get('client') or '—'} &nbsp;|&nbsp;
                    {project.get('start_date', '?')} → {project.get('end_date', '?')}</span>
                </div>
                <div style="display:flex; gap:1.5rem; align-items:center; flex-wrap:wrap;">
                    <div style="text-align:center; background:rgba(255,255,255,0.1);
                         border-radius:8px; padding:0.5rem 1rem;">
                        <div style="font-size:0.75rem; color:#aaa;">Sample Target</div>
                        <div style="font-size:1.4rem; font-weight:700;">{target:,}</div>
                        <div style="font-size:0.75rem; color:#aaa;">Achieved: {approved_count:,}
                            &nbsp;<span style="color:{overflow_color}; font-weight:700;">{overflow_str}</span>
                        </div>
                    </div>
                    <div style="text-align:center; background:rgba(255,255,255,0.1);
                         border-radius:8px; padding:0.5rem 1rem;">
                        <div style="font-size:0.75rem; color:#aaa;">{bc_icon} Back-checks</div>
                        <div style="font-size:1.4rem; font-weight:700;">{bc_rate}%</div>
                        <div style="font-size:0.75rem; color:#aaa;">Target: {bc_target_pct}%</div>
                    </div>
                    <div style="text-align:center; background:rgba(255,255,255,0.1);
                         border-radius:8px; padding:0.5rem 1rem;">
                        <div style="font-size:0.75rem; color:#aaa;">{li_icon} Listen-in</div>
                        <div style="font-size:1.4rem; font-weight:700;">{li_rate}%</div>
                        <div style="font-size:0.75rem; color:#aaa;">Target: {li_target_pct}%</div>
                    </div>
                    <div>
                        <span style="background:{status_color}; color:white; border-radius:6px;
                               padding:4px 14px; font-size:0.85rem;">{project['status'].upper()}</span>
                    </div>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Sub-tabs
    tab_labels = [t[0] for t in TABS]
    selected_tab = st.session_state.get("project_tab", "quality_report")
    selected_idx = next((i for i, t in enumerate(TABS) if t[1] == selected_tab), 0)

    tabs = st.tabs(tab_labels)
    tab_modules = [
        quality_report, backcheck_report, cancelled_interviews,
        performance_report, timing_report, listen_in, wave_comparison,
    ]
    for i, (tab, module) in enumerate(zip(tabs, tab_modules)):
        with tab:
            module.show(project_id)
