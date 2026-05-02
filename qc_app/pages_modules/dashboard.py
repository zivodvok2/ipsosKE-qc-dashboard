import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import database as db
from config import IPSOS_NAVY, IPSOS_TEAL, IPSOS_ORANGE, IPSOS_YELLOW, CHART_COLORS, DRILLDOWN_ROLES
from utils.charts import kpi_card, bar_chart


REPORT_LABELS = {
    "quality_report": "Quality Report",
    "backcheck": "Back-check Report",
    "cancelled_interviews": "Cancelled Interviews",
    "performance": "Performance Report",
    "timing": "Timing Report",
    "listen_in": "Listen-in",
}


def _risk_alerts(summary: list[dict]):
    """Compute and display risk alerts from project summary data."""
    alerts = []
    today = date.today()

    for s in summary:
        if s["status"] != "active":
            continue

        name = s["name"]

        # Completion risk: < 50% done with end date approaching
        try:
            end = date.fromisoformat(str(s.get("end_date", "")))
            days_left = (end - today).days
            if days_left <= 7 and s["completion_pct"] < 80:
                alerts.append(("critical", name,
                                f"End date in {days_left} day(s) — only {s['completion_pct']}% complete"))
            elif days_left <= 14 and s["completion_pct"] < 50:
                alerts.append(("warning", name,
                                f"End date in {days_left} days — only {s['completion_pct']}% complete"))
        except Exception:
            pass

        # Back-check below target
        bc_target = round((s.get("backcheck_target") or 0.20) * 100)
        if s["backcheck_rate"] < bc_target:
            alerts.append(("warning", name,
                            f"Back-check rate {s['backcheck_rate']}% below target {bc_target}%"))

        # High error / flagged rate — use project-specific thresholds if set
        total = s.get("total_submitted", 0) or (s.get("approved", 0) + s.get("flagged", 0))
        warn_thresh = s.get("flag_warning_pct") or 5.0
        crit_thresh = s.get("flag_critical_pct") or 10.0
        if total > 0:
            flag_pct = round(s["flagged"] / total * 100, 1)
            if flag_pct >= crit_thresh:
                alerts.append(("critical", name,
                                f"High flagged rate: {flag_pct}% of submitted records flagged"))
            elif flag_pct >= warn_thresh:
                alerts.append(("warning", name,
                                f"Elevated flagged rate: {flag_pct}% of submitted records"))

        # No data uploaded yet
        if s["approved"] == 0:
            alerts.append(("info", name, "No approved interviews uploaded yet"))

    if not alerts:
        return

    st.markdown("---")
    st.markdown(
        f'<h3 style="color:{IPSOS_NAVY};">Risk & Alert Status</h3>',
        unsafe_allow_html=True,
    )

    icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
    bg = {"critical": "#FFF3F3", "warning": "#FFFBEA", "info": "#F0F7FF"}
    border = {"critical": IPSOS_ORANGE, "warning": IPSOS_YELLOW, "info": IPSOS_TEAL}

    for level, project_name, message in alerts:
        st.markdown(
            f"""<div style="background:{bg[level]}; border-left:4px solid {border[level]};
                 padding:0.6rem 1rem; margin:4px 0; border-radius:4px; font-size:0.9rem;">
                {icons[level]} <strong>{project_name}</strong> — {message}
            </div>""",
            unsafe_allow_html=True,
        )


def _activity_feed():
    """Show recent upload activity across all projects."""
    activities = db.get_project_activity(limit=10)
    if not activities:
        return

    st.markdown("---")
    st.markdown(
        f'<h3 style="color:{IPSOS_NAVY};">Recent Activity</h3>',
        unsafe_allow_html=True,
    )

    for act in activities:
        report_label = REPORT_LABELS.get(act["report_type"], act["report_type"])
        wave_str = f" · Wave: {act['wave_label']}" if act.get("wave_label") else ""
        uploader = act.get("uploader") or "System"
        try:
            dt = datetime.fromisoformat(str(act["upload_date"]))
            dt_str = dt.strftime("%d %b %Y, %H:%M")
        except Exception:
            dt_str = str(act["upload_date"])[:16]

        st.markdown(
            f"""<div style="display:flex; justify-content:space-between; align-items:center;
                 padding:0.4rem 0.8rem; margin:2px 0; background:white;
                 border-radius:6px; box-shadow:0 1px 3px rgba(0,0,0,0.06); font-size:0.85rem;">
                <div>
                    <span style="color:{IPSOS_TEAL}; font-weight:600;">{act['project_name']}</span>
                    &nbsp;·&nbsp;{report_label}{wave_str}
                    &nbsp;·&nbsp;<span style="color:#666;">{act['row_count']:,} rows</span>
                </div>
                <div style="color:#999; font-size:0.8rem;">{uploader} &nbsp;·&nbsp; {dt_str}</div>
            </div>""",
            unsafe_allow_html=True,
        )


def show():
    st.markdown(
        f'<h2 style="color:{IPSOS_NAVY}; border-bottom: 3px solid {IPSOS_TEAL}; padding-bottom:0.4rem;">Project Dashboard</h2>',
        unsafe_allow_html=True,
    )

    user_id = st.session_state["user_id"]
    role = st.session_state["user_role"]
    projects = db.get_user_projects(user_id, role)

    if not projects:
        st.info("No projects found. Ask your QC Executive to assign you to a project.")
        return

    summary = db.get_dashboard_summary()
    # Filter summary to only projects visible to this user
    visible_ids = {p["id"] for p in projects}
    summary = [s for s in summary if s["id"] in visible_ids]

    # ── KPI summary row ────────────────────────────────────────────────────
    active = sum(1 for s in summary if s["status"] == "active")
    total_target = sum(s["sample_target"] or 0 for s in summary if s["status"] == "active")
    total_approved = sum(s["approved"] for s in summary if s["status"] == "active")
    total_flagged = sum(s["flagged"] for s in summary if s["status"] == "active")
    avg_bc_rate = (
        sum(s["backcheck_rate"] for s in summary if s["status"] == "active") / active
        if active else 0
    )

    cols = st.columns(5)
    cards = [
        ("Active Projects", active, "", IPSOS_NAVY),
        ("Sample Target", f"{total_target:,}", "", IPSOS_TEAL),
        ("Approved Interviews", f"{total_approved:,}", "", IPSOS_TEAL),
        ("Avg. Back-check Rate", f"{avg_bc_rate:.1f}", "%", "#7E57C2"),
        ("Total Flagged Records", f"{total_flagged:,}", "", IPSOS_ORANGE),
    ]
    for col, (label, val, suf, color) in zip(cols, cards):
        col.markdown(kpi_card(label, val, suffix=suf, color=color), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Search + Filters ───────────────────────────────────────────────────
    search_col, _ = st.columns([2, 3])
    with search_col:
        search_term = st.text_input(
            "Search projects", placeholder="Search by name, job number, or client…",
            key="dash_search", label_visibility="collapsed"
        )

    f1, f2, f3, f4, f5 = st.columns([2, 2, 1, 1, 1])
    with f1:
        status_filter = st.multiselect(
            "Status", ["active", "completed", "paused"],
            default=["active"], key="dash_status"
        )
    with f2:
        clients = sorted({s.get("client") or "" for s in summary if s.get("client")})
        client_filter = st.multiselect("Client", clients, key="dash_client")
    with f3:
        sort_by = st.selectbox(
            "Sort by", ["Name", "Completion %", "Sample Target", "Job No."], key="dash_sort"
        )
    with f4:
        date_from = st.date_input("End date from", value=None, key="dash_date_from")
    with f5:
        date_to = st.date_input("End date to", value=None, key="dash_date_to")

    df = pd.DataFrame(summary)

    # Live search
    if search_term:
        term = search_term.lower()
        mask = (
            df["name"].fillna("").str.lower().str.contains(term, na=False)
            | df.get("client", pd.Series(dtype=str)).fillna("").str.lower().str.contains(term, na=False)
            | df.get("job_number", pd.Series(dtype=str)).fillna("").str.lower().str.contains(term, na=False)
        )
        df = df[mask]

    if status_filter:
        df = df[df["status"].isin(status_filter)]
    if client_filter:
        df = df[df["client"].isin(client_filter)]

    # Date range filter — keeps projects whose end_date falls within the range
    if date_from and "end_date" in df.columns:
        df = df[pd.to_datetime(df["end_date"], errors="coerce") >= pd.Timestamp(date_from)]
    if date_to and "end_date" in df.columns:
        df = df[pd.to_datetime(df["end_date"], errors="coerce") <= pd.Timestamp(date_to)]

    if df.empty:
        st.warning("No projects match the current filter.")
        return

    sort_map = {
        "Name": "name",
        "Completion %": "completion_pct",
        "Sample Target": "sample_target",
        "Job No.": "job_number",
    }
    df = df.sort_values(sort_map[sort_by], ascending=(sort_by in ("Name", "Job No.")), na_position="last")

    # ── Completion bar chart ───────────────────────────────────────────────
    st.markdown("### Completion vs. Target by Project")
    fig_data = []
    for _, row in df.iterrows():
        fig_data.append({"Project": row["name"], "Count": row["sample_target"] or 0, "Series": "Target"})
        fig_data.append({"Project": row["name"], "Count": row["approved"], "Series": "Approved"})
    fig_df = pd.DataFrame(fig_data)
    fig = px.bar(fig_df, x="Project", y="Count", color="Series", barmode="group",
                 color_discrete_map={"Target": IPSOS_NAVY, "Approved": IPSOS_TEAL},
                 height=350)
    fig.update_layout(paper_bgcolor="white", plot_bgcolor="#F5F5F5",
                      margin=dict(l=20, r=20, t=20, b=80),
                      legend=dict(orientation="h", y=1.05))
    st.plotly_chart(fig, use_container_width=True, key="dash_completion_chart")

    # ── Project table ──────────────────────────────────────────────────────
    st.markdown("### All Projects")
    can_drilldown = role in DRILLDOWN_ROLES

    for _, row in df.iterrows():
        pid = row["id"]
        pct = row["completion_pct"]
        status_color = {"active": "#2E7D32", "completed": "#1565C0", "paused": "#E65100"}.get(row["status"], "#666")
        bc_color = IPSOS_TEAL if row["backcheck_rate"] >= 20 else IPSOS_ORANGE
        bc_icon = "✅" if row["backcheck_rate"] >= 20 else "⚠️"

        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1, 1, 1, 1])
            with c1:
                job_tag = f'&nbsp;<span style="color:#888;font-size:0.75rem;">[{row["job_number"]}]</span>' if row.get("job_number") else ""
                st.markdown(
                    f'<span style="font-weight:600;font-size:1rem;">{row["name"]}</span>'
                    f'{job_tag}'
                    f'&nbsp;&nbsp;<span style="background:{status_color};color:white;'
                    f'border-radius:4px;padding:2px 8px;font-size:0.7rem;">'
                    f'{row["status"].upper()}</span>',
                    unsafe_allow_html=True,
                )
                client = row.get("client") or "—"
                st.caption(f"Client: {client}")
            with c2:
                st.progress(min(pct / 100, 1.0))
                st.caption(f"{row['approved']:,} / {row['sample_target'] or 0:,} ({pct}%)")
            with c3:
                st.metric("BC Rate", f"{row['backcheck_rate']}%")
            with c4:
                li_rate = row.get("listenin_rate", 0)
                st.metric("Listen-in Rate", f"{li_rate}%")
            with c5:
                st.metric("Flagged", f"{row['flagged']:,}")
            with c6:
                if can_drilldown and db.user_can_drilldown(
                    st.session_state["user_id"], pid, role
                ):
                    if st.button("View Details", key=f"drill_{pid}", use_container_width=True):
                        st.session_state["page"] = "project_detail"
                        st.session_state["project_id"] = pid
                        st.session_state["project_tab"] = "quality_report"
                        st.rerun()
                else:
                    st.markdown(
                        '<span style="color:#999;font-size:0.8rem;">Summary only</span>',
                        unsafe_allow_html=True,
                    )
            st.divider()

    # ── Risk Alerts ────────────────────────────────────────────────────────
    _risk_alerts(summary)

    # ── Activity Feed ──────────────────────────────────────────────────────
    _activity_feed()
