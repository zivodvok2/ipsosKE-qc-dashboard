import streamlit as st
import pandas as pd
import database as db
import auth as auth_module
from config import IPSOS_NAVY, IPSOS_TEAL, ROLES, ADMIN_ROLES
from utils.exports import to_excel_bytes


def show():
    st.markdown(
        f'<h2 style="color:{IPSOS_NAVY}; border-bottom: 3px solid {IPSOS_TEAL}; padding-bottom:0.4rem;">Admin Panel</h2>',
        unsafe_allow_html=True,
    )

    role = st.session_state["user_role"]
    if role not in ADMIN_ROLES:
        st.error("Access denied. Admins only.")
        return

    tab_users, tab_projects, tab_assignments, tab_uploads = st.tabs(
        ["User Management", "Project Management", "Project Assignments", "Upload History"]
    )

    # ── User Management ────────────────────────────────────────────────────
    with tab_users:
        st.markdown("### Users")
        users = db.get_all_users()
        df = pd.DataFrame(users)[["id", "email", "full_name", "role", "is_active", "created_at"]]
        df.columns = ["ID", "Email", "Name", "Role", "Active", "Created"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Change User Role")
            user_opts = {f"{u['full_name']} ({u['email']})": u["id"] for u in users}
            selected_label = st.selectbox("Select User", list(user_opts.keys()), key="role_user")
            new_role = st.selectbox("New Role", list(ROLES.keys()),
                                    format_func=lambda r: ROLES[r], key="role_new")
            if st.button("Update Role", key="role_btn"):
                db.update_user_role(user_opts[selected_label], new_role)
                st.success("Role updated.")
                st.rerun()

        with col2:
            st.markdown("#### Activate / Deactivate User")
            sel2 = st.selectbox("Select User", list(user_opts.keys()), key="act_user")
            action = st.radio("Action", ["Activate", "Deactivate"], horizontal=True, key="act_radio")
            if st.button("Apply", key="act_btn"):
                db.toggle_user_active(user_opts[sel2], 1 if action == "Activate" else 0)
                st.success(f"User {action.lower()}d.")
                st.rerun()

        st.markdown("#### Add New User (Admin)")
        with st.form("admin_add_user"):
            a_name = st.text_input("Full Name")
            a_email = st.text_input("Email")
            a_role = st.selectbox("Role", list(ROLES.keys()), format_func=lambda r: ROLES[r])
            a_pass = st.text_input("Temporary Password", type="password")
            submitted = st.form_submit_button("Create User")
        if submitted:
            if not all([a_name, a_email, a_role, a_pass]):
                st.error("All fields required.")
            elif len(a_pass) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                ok, err = db.create_user(
                    a_email.strip().lower(),
                    auth_module.hash_password(a_pass),
                    a_name.strip(),
                    a_role,
                    st.session_state["user_id"],
                )
                if ok:
                    st.success(f"User {a_name} created with role {ROLES[a_role]}.")
                    st.rerun()
                else:
                    st.error(err)

    # ── Project Management ─────────────────────────────────────────────────
    with tab_projects:
        st.markdown("### Projects")
        projects = db.get_all_projects()
        if projects:
            df = pd.DataFrame(projects)[[
                "id", "name", "client", "sample_target", "status", "start_date", "end_date"
            ]]
            df.columns = ["ID", "Name", "Client", "Target", "Status", "Start", "End"]
            st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### Add New Project")
        with st.form("add_project_form"):
            p_name = st.text_input("Project Name *")
            p_client = st.text_input("Client / Study Name")
            p_target = st.number_input("Sample Target", min_value=0, value=1000, step=50)
            c1, c2 = st.columns(2)
            p_start = c1.date_input("Start Date")
            p_end = c2.date_input("End Date")
            c3, c4, c5 = st.columns(3)
            p_bc = c3.slider("Back-check Target (%)", 5, 50, 20) / 100
            p_li = c4.slider("Listen-in Target (%)", 5, 30, 10) / 100
            p_acc = c5.slider("Accompaniment Target (%)", 5, 50, 20) / 100
            submitted_p = st.form_submit_button("Create Project")
        if submitted_p:
            if not p_name:
                st.error("Project name is required.")
            else:
                db.create_project(
                    p_name, p_client, p_target,
                    str(p_start), str(p_end),
                    p_bc, p_li, p_acc,
                    st.session_state["user_id"],
                )
                st.success(f"Project '{p_name}' created.")
                st.rerun()

        st.markdown("#### Edit Project")
        if projects:
            proj_opts = {p["name"]: p["id"] for p in projects}
            sel_proj = st.selectbox("Select Project to Edit", list(proj_opts.keys()), key="edit_proj")
            sel_pid = proj_opts[sel_proj]
            cur = next(p for p in projects if p["id"] == sel_pid)

            with st.form("edit_project_form"):
                from datetime import date as _date
                def _parse_date(s):
                    try:
                        return _date.fromisoformat(str(s))
                    except Exception:
                        return _date.today()

                e_name   = st.text_input("Project Name *", value=cur["name"])
                e_client = st.text_input("Client / Study Name", value=cur.get("client") or "")
                e_target = st.number_input("Sample Target", min_value=0,
                                           value=int(cur.get("sample_target") or 0), step=50)
                ec1, ec2 = st.columns(2)
                e_start  = ec1.date_input("Start Date", value=_parse_date(cur.get("start_date")))
                e_end    = ec2.date_input("End Date",   value=_parse_date(cur.get("end_date")))
                ec3, ec4, ec5 = st.columns(3)
                e_bc  = ec3.slider("Back-check Target (%)",   5, 50, int(round((cur.get("backcheck_target")    or 0.20) * 100))) / 100
                e_li  = ec4.slider("Listen-in Target (%)",    5, 30, int(round((cur.get("listenin_target")     or 0.10) * 100))) / 100
                e_acc = ec5.slider("Accompaniment Target (%)", 5, 50, int(round((cur.get("accompaniment_target") or 0.20) * 100))) / 100
                e_status = st.selectbox("Status", ["active", "paused", "completed"],
                                        index=["active", "paused", "completed"].index(cur.get("status", "active")))
                save_edit = st.form_submit_button("Save Changes", use_container_width=True)

            if save_edit:
                if not e_name:
                    st.error("Project name is required.")
                else:
                    db.update_project(
                        sel_pid,
                        name=e_name, client=e_client, sample_target=e_target,
                        start_date=str(e_start), end_date=str(e_end),
                        backcheck_target=e_bc, listenin_target=e_li,
                        accompaniment_target=e_acc, status=e_status,
                    )
                    st.success(f"Project '{e_name}' updated.")
                    st.rerun()

    # ── Project Assignments ────────────────────────────────────────────────
    with tab_assignments:
        st.markdown("### Project Assignments")
        projects = db.get_all_projects()
        users = db.get_all_users()

        if not projects:
            st.info("No projects yet.")
        else:
            proj_opts = {p["name"]: p["id"] for p in projects}
            sel = st.selectbox("Select Project", list(proj_opts.keys()), key="assign_proj")
            pid = proj_opts[sel]
            assignees = db.get_project_assignees(pid)

            st.markdown(f"**Currently assigned ({len(assignees)}):**")
            for a in assignees:
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.write(f"{a['full_name']} ({a['email']})")
                c2.caption(ROLES.get(a["role"], a["role"]))
                if c3.button("Remove", key=f"rm_{pid}_{a['id']}"):
                    db.remove_user_from_project(pid, a["id"])
                    st.rerun()

            st.markdown("**Assign users:**")
            assigned_ids = {a["id"] for a in assignees}
            unassigned = [u for u in users if u["id"] not in assigned_ids]
            if unassigned:
                user_opts = {f"{u['full_name']} ({u['email']})": u["id"] for u in unassigned}
                to_add = st.multiselect("Select users to assign", list(user_opts.keys()), key="assign_users")
                if st.button("Assign Selected", key="assign_btn"):
                    for label in to_add:
                        db.assign_user_to_project(pid, user_opts[label], st.session_state["user_id"])
                    st.success("Users assigned.")
                    st.rerun()
            else:
                st.caption("All users are already assigned to this project.")

    # ── Upload History ─────────────────────────────────────────────────────
    with tab_uploads:
        st.markdown("### Upload History (All Projects)")
        logs = db.get_upload_log()
        if logs:
            log_df = pd.DataFrame(logs)[[
                "project_name", "report_type", "filename", "row_count",
                "uploader_name", "upload_date", "upload_id"
            ]]
            log_df.columns = ["Project", "Type", "File", "Rows", "Uploader", "Date", "Upload ID"]
            st.dataframe(log_df, use_container_width=True, hide_index=True)

            st.markdown("#### Delete an Upload")
            upload_opts = {
                f"{l['project_name']} — {l['report_type']} — {l['filename']} ({l['upload_date'][:10]})": (
                    l["upload_id"], l["report_type"]
                )
                for l in logs
            }
            sel_log = st.selectbox("Select Upload to Delete", list(upload_opts.keys()), key="del_upload")
            if st.button("Delete Upload", type="secondary"):
                uid, rtype = upload_opts[sel_log]
                db.delete_upload(uid, rtype)
                st.success("Upload deleted.")
                st.rerun()
        else:
            st.info("No uploads yet.")
