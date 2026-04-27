"""
Seed script -- inserts 3 realistic test projects with full data for prototyping.
Run from the project root:  python seed_data.py
"""

import sys, os, random, uuid
from datetime import date, timedelta

ROOT    = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT, "qc_app")
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)   # so DB_PATH resolves to qc_app/qc_dashboard.db

import database as db

random.seed(42)

# ── helpers ────────────────────────────────────────────────────────────────

def rdate(start: date, end: date) -> str:
    return str(start + timedelta(days=random.randint(0, (end - start).days)))

def rtime(h0=8, h1=17):
    return f"{random.randint(h0,h1-1):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"

def add_minutes(t: str, mins: float) -> str:
    h, m, s = map(int, t.split(":"))
    total = h*3600 + m*60 + s + int(mins*60)
    return f"{total//3600:02d}:{(total%3600)//60:02d}:{total%60:02d}"

ADMIN_ID = None   # will be filled after db.init_db()

# ── project definitions ────────────────────────────────────────────────────

PROJECTS = [
    {
        "name": "Consumer Satisfaction Survey 2025",
        "client": "Unilever Kenya",
        "sample_target": 500,
        "start_date": "2025-02-01",
        "end_date": "2025-05-31",
        "status": "active",
        "backcheck_target": 0.20,
        "listenin_target": 0.10,
        "accompaniment_target": 0.20,
        "regions": ["Nairobi", "Mombasa", "Kisumu", "Nakuru"],
        "interviewers": ["NB0664", "NB0712", "MSA0234", "KSM0891", "NAK0445", "NB0991"],
        # wave, start, end, n_interviews, flagged_pct, approved_pct
        "waves": [
            ("Wave 1", date(2025,2,1),  date(2025,2,28),  120, 0.083, 0.82),
            ("Wave 2", date(2025,3,1),  date(2025,3,31),  180, 0.055, 0.87),
            ("Wave 3", date(2025,4,1),  date(2025,4,25),  150, 0.047, 0.89),
        ],
    },
    {
        "name": "National Youth Survey 2025",
        "client": "UNICEF Kenya",
        "sample_target": 800,
        "start_date": "2025-03-01",
        "end_date": "2025-06-30",
        "status": "active",
        "backcheck_target": 0.25,
        "listenin_target": 0.15,
        "accompaniment_target": 0.25,
        "regions": ["Nairobi", "Kisumu", "Eldoret", "Meru", "Nyeri"],
        "interviewers": ["NB1001", "NB1002", "KSM1003", "ELD1004", "MER1005", "NYR1006", "NB1007", "KSM1008"],
        "waves": [
            ("Wave 1", date(2025,3,1),  date(2025,3,31),  200, 0.060, 0.84),
            ("Wave 2", date(2025,4,1),  date(2025,4,30),  180, 0.078, 0.85),
        ],
    },
    {
        "name": "Media Habits Tracker Q1 2025",
        "client": "Nation Media Group",
        "sample_target": 300,
        "start_date": "2025-01-15",
        "end_date": "2025-03-31",
        "status": "completed",
        "backcheck_target": 0.20,
        "listenin_target": 0.10,
        "accompaniment_target": 0.20,
        "regions": ["Nairobi", "Mombasa"],
        "interviewers": ["NB0501", "NB0502", "MSA0503", "NB0504"],
        "waves": [
            ("Wave 1", date(2025,1,15), date(2025,1,31), 80,  0.092, 0.81),
            ("Wave 2", date(2025,2,1),  date(2025,2,28), 120, 0.058, 0.88),
            ("Wave 3", date(2025,3,1),  date(2025,3,31), 115, 0.042, 0.91),
        ],
    },
]


# ── quality records ────────────────────────────────────────────────────────

def gen_quality_records(project_id, interviewers, regions, wave_label,
                        start, end, n, flagged_pct, approved_pct):
    n_flagged  = round(n * flagged_pct)
    n_approved = round(n * approved_pct)
    n_cancelled = round(n * 0.04)
    n_pending  = n - n_approved - n_cancelled

    avg_dur = random.uniform(22, 35)
    records = []
    for i in range(n):
        iv = random.choice(interviewers)
        reg = random.choice(regions)
        d = rdate(start, end)
        st = rtime(8, 16)
        dur = max(5.0, random.gauss(avg_dur, avg_dur * 0.25))
        et = add_minutes(st, dur)

        if i < n_flagged:
            dflag = "Flag"
        else:
            dflag = "Okay"

        if i < n_approved:
            status = "Approved"
        elif i < n_approved + n_pending:
            status = "Pending"
        else:
            status = "Cancelled"

        sl = "0" if random.random() > 0.04 else "Straight-lining detected"
        lp = "0" if random.random() > 0.03 else "Long pause > 10s"

        gps_r = random.random()
        gps = "Present" if gps_r > 0.07 else ("Missing" if gps_r > 0.02 else "Duplicate")
        phone  = "Yes" if random.random() > 0.05 else "No"
        audio  = "Yes" if random.random() > 0.04 else "No"

        records.append({
            "instance_id":          f"ID{project_id}{i+1:05d}",
            "interviewer_id":       iv,
            "interview_date":       d,
            "start_time":           st,
            "end_time":             et,
            "duration_minutes":     round(dur, 1),
            "duration_flag":        dflag,
            "straight_lining":      sl,
            "long_pause":           lp,
            "gps_status":           gps,
            "phone_present":        phone,
            "audio_present":        audio,
            "region":               reg,
            "location":             f"{reg} Zone {random.randint(1,5)}",
            "sample_point_id":      f"{reg[:2].upper()}{random.randint(10,99)}",
            "approval_status":      status,
            "qc_comments":          "",
        })

    random.shuffle(records)
    db.insert_quality_records(project_id, ADMIN_ID, f"quality_{wave_label}.xlsx",
                              records, wave_label=wave_label)
    approved = [r for r in records if r["approval_status"] == "Approved"]
    print(f"    QR {wave_label}: {n} records, {len(approved)} approved, "
          f"{n_flagged} flagged ({flagged_pct*100:.1f}%)")
    return approved


# ── back-check records ─────────────────────────────────────────────────────

def gen_backcheck_records(project_id, approved_records, wave_label,
                          bc_rate_target, start, end):
    n_bc = round(len(approved_records) * bc_rate_target)
    sample = random.sample(approved_records, min(n_bc, len(approved_records)))
    bc_records = []
    for r in sample:
        err = {f"error_{i:02d}": 0 for i in range(1, 14)}
        roll = random.random()
        if roll < 0.15:
            err["error_07"] = 1   # Engaged / answer machine
        elif roll < 0.25:
            err["error_08"] = 1   # Refused / unable to reach
        elif roll < 0.30:
            err["error_09"] = 1   # Doesn't remember interview
        elif roll < 0.32:
            err["error_05"] = 1   # Wrong telephone number
        elif roll < 0.33:
            err["error_01"] = 1   # Fraudulent (rare)

        bc_records.append({
            "bc_instance_id":       f"BC{r['instance_id']}",
            "original_instance_id": r["instance_id"],
            "interview_status":     "Completed - Pending Export",
            "region":               r["region"],
            "location":             r["location"],
            "sample_point_id":      r["sample_point_id"],
            "backchecker_id":       f"BC{random.choice(['LE0018','LE0024','LE0031'])}",
            "interviewer_id":       r["interviewer_id"],
            "script_name":          "Project Survey",
            "interview_date":       r["interview_date"],
            "interview_start_time": r["start_time"],
            "backcheck_date":       rdate(
                date.fromisoformat(r["interview_date"]) + timedelta(days=1),
                max(date.fromisoformat(r["interview_date"]) + timedelta(days=1),
                    end + timedelta(days=7)),
            ),
            "backcheck_time":       rtime(8, 17),
            **err,
        })
    db.insert_backcheck_records(project_id, ADMIN_ID,
                                f"backcheck_{wave_label}.xlsx",
                                bc_records, wave_label=wave_label)
    bc_rate = round(len(bc_records) / len(approved_records) * 100, 1) if approved_records else 0
    print(f"    BC  {wave_label}: {len(bc_records)} back-checks ({bc_rate}%)")
    return bc_records


# ── performance records ────────────────────────────────────────────────────

def gen_performance_records(project_id, approved_records, wave_label,
                             bc_records, interviewers):
    by_iv = {}
    for r in approved_records:
        iv = r["interviewer_id"]
        if iv not in by_iv:
            dates = []
            by_iv[iv] = {"dates": dates, "completes": 0, "region": r["region"]}
        by_iv[iv]["completes"] += 1
        by_iv[iv]["dates"].append(r["interview_date"])

    bc_by_iv = {}
    for b in bc_records:
        iv = b["interviewer_id"]
        bc_by_iv[iv] = bc_by_iv.get(iv, 0) + 1

    perf = []
    for iv, data in by_iv.items():
        completes = data["completes"]
        bc_done   = bc_by_iv.get(iv, 0)
        acc       = round(completes * random.uniform(0.08, 0.30))
        tel_bc    = round(bc_done * random.uniform(0.55, 0.75))
        f2f_bc    = bc_done - tel_bc
        sorted_dates = sorted(data["dates"])
        perf.append({
            "interviewer_id":             iv,
            "region":                     data["region"],
            "first_interview":            sorted_dates[0] if sorted_dates else "",
            "last_interview":             sorted_dates[-1] if sorted_dates else "",
            "interview_completes":        completes,
            "followup_completes":         round(completes * random.uniform(0.02, 0.08)),
            "ecs_completes":              round(completes * random.uniform(0.01, 0.05)),
            "work_summary":               completes,
            "accompaniments":             acc,
            "cancelled_interviews":       random.randint(0, 3),
            "backcheck_telephone_created":tel_bc,
            "backcheck_f2f_created":      f2f_bc,
            "backcheck_f2f_infield":      round(f2f_bc * 0.6),
            "backcheck_total":            bc_done,
            "backcheck_completed":        bc_done,
        })
    db.insert_performance_records(project_id, ADMIN_ID,
                                  f"performance_{wave_label}.xlsx",
                                  perf, wave_label=wave_label)
    print(f"    PF  {wave_label}: {len(perf)} interviewers")


# ── listen-in records ──────────────────────────────────────────────────────

LISTEN_TYPES  = ["Telephone", "F2F / Accompaniment", "Audio Playback"]
LISTEN_ISSUES = [
    "Interviewer skipped key probes",
    "Background noise affecting audio quality",
    "Respondent appeared rushed — short answers",
    "Interviewer read out response options prematurely",
    "",
]

def gen_listenin_records(project_id, approved_records, wave_label,
                          li_rate_target, start, end):
    n_li = round(len(approved_records) * li_rate_target)
    sample = random.sample(approved_records, min(n_li, len(approved_records)))
    records = []
    for r in sample:
        roll = random.random()
        result = "Pass" if roll > 0.18 else ("Partial" if roll > 0.06 else "Fail")
        issue  = random.choice(LISTEN_ISSUES) if result != "Pass" else ""
        action = "Debrief conducted with interviewer" if issue else ""
        records.append({
            "instance_id":    r["instance_id"],
            "interviewer_id": r["interviewer_id"],
            "region":         r["region"],
            "listen_date":    rdate(date.fromisoformat(r["interview_date"]),
                                    min(end, date.fromisoformat(r["interview_date"]) + timedelta(days=7))),
            "listen_type":    random.choice(LISTEN_TYPES),
            "result":         result,
            "issues_noted":   issue,
            "action_taken":   action,
        })
    db.insert_listen_in_batch(project_id, ADMIN_ID,
                               f"listenin_{wave_label}.xlsx",
                               records, wave_label=wave_label)
    li_rate = round(len(records) / len(approved_records) * 100, 1) if approved_records else 0
    print(f"    LI  {wave_label}: {len(records)} sessions ({li_rate}%)")


# ── cancelled interviews ───────────────────────────────────────────────────

def gen_cancelled_records(project_id, approved_records, wave_label):
    n_canc = max(3, round(len(approved_records) * random.uniform(0.02, 0.06)))
    sample = random.sample(approved_records, min(n_canc, len(approved_records)))
    records = []
    for r in sample:
        dur = random.uniform(2, 8)
        records.append({
            "instance_id":              r["instance_id"],
            "region":                   r["region"],
            "location":                 r["location"],
            "sample_point_id":          r["sample_point_id"],
            "interviewer_id":           r["interviewer_id"],
            "script_name":              "Project Survey",
            "interview_date":           r["interview_date"],
            "start_time":               r["start_time"],
            "end_time":                 add_minutes(r["start_time"], dur),
            "interview_length":         round(dur, 1),
            "active_length":            round(dur * 0.7, 1),
            "avg_length_sample_point":  round(random.uniform(20, 30), 1),
            "avg_length_region":        round(random.uniform(22, 32), 1),
            "avg_length_project":       round(random.uniform(23, 31), 1),
            "idle_time":                round(random.uniform(0, 5), 1),
            "gap_to_last":              round(random.uniform(30, 600), 0),
            "same_day_finish":          random.choice(["Yes", "No"]),
            "qf_a": random.choice(["", "", "", "1"]),
            "qf_b": random.choice(["", "", "1"]),
            "qf_c": "",
            "qf_d": "",
            "qf_e": "",
            "qf_f": "",
            "interviewer_performance":  random.choice(["Good", "Average", "Poor"]),
            "backcheck_result_telephone": "",
            "backcheck_result_f2f": "",
            "backcheck_result_independent": "",
        })
    db.insert_cancelled_records(project_id, ADMIN_ID,
                                 f"cancelled_{wave_label}.xlsx",
                                 records, wave_label=wave_label)
    print(f"    CI  {wave_label}: {len(records)} cancellations")


# ── main ───────────────────────────────────────────────────────────────────

def main():
    global ADMIN_ID

    db.init_db()

    # Get admin user id
    admin = db.get_user_by_email("admin@ipsos.com")
    ADMIN_ID = admin["id"] if admin else None

    for pdef in PROJECTS:
        # Create project
        db.create_project(
            pdef["name"], pdef["client"], pdef["sample_target"],
            pdef["start_date"], pdef["end_date"],
            pdef["backcheck_target"], pdef["listenin_target"],
            pdef["accompaniment_target"], ADMIN_ID,
        )
        # Find the project id just created
        all_p = db.get_all_projects()
        project = next(p for p in all_p if p["name"] == pdef["name"])
        pid = project["id"]

        # Set status
        db.update_project(pid, status=pdef["status"])

        print(f"\n[{pdef['name']}]  id={pid}")

        for wave_label, wstart, wend, n_int, flagged_pct, approved_pct in pdef["waves"]:
            print(f"  {wave_label}")

            # BC target varies slightly wave-to-wave for realism
            bc_tgt = pdef["backcheck_target"] + random.uniform(-0.03, 0.05)
            li_tgt = pdef["listenin_target"]  + random.uniform(-0.02, 0.04)

            approved = gen_quality_records(
                pid, pdef["interviewers"], pdef["regions"],
                wave_label, wstart, wend, n_int, flagged_pct, approved_pct,
            )
            bc_recs = gen_backcheck_records(
                pid, approved, wave_label, bc_tgt, wstart, wend,
            )
            gen_performance_records(
                pid, approved, wave_label, bc_recs, pdef["interviewers"],
            )
            gen_listenin_records(
                pid, approved, wave_label, li_tgt, wstart, wend,
            )
            gen_cancelled_records(pid, approved, wave_label)

    print("\nDone. Restart the Streamlit app to see the seeded data.")


if __name__ == "__main__":
    main()
