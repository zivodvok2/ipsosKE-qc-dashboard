# IpsosKE QC Dashboard — Developer Guide

## Project Overview

A Quality Control monitoring dashboard for Ipsos Kenya operations. Internal use only.
Built in **Python + Streamlit** for prototype; targets server deployment later.

**Source brief:** QC Dashboard Write-up, April 2025 (Ipsos Kenya internal document).

**Goals:**
- Near-real-time project health monitoring, activity tracking, risk alerts, QC KPI reporting.
- Quick-read consumable pieces of information and statistics.
- Engaging, easy-to-use, and decision-making focused.
- Executive overview of project health and milestones.
- Accessible on both mobile handsets (insights on the go) and laptop/desktop.

---

## Core Functionality Components (from Write-up)

### Activity Tracking
General overview of all project-related activities: launch, approval status, back-check and
audio listen-in efforts, deadlines, and upcoming events (coding, analysis, final reporting).
Implemented as a live activity feed on the main dashboard showing recent uploads and an
alerting system for risk flags. Alerts are computed from project metrics vs targets and deadlines.

### Project Deliverables
Real-time progress of each quality control project deliverable. Flags blocked deliverables.
Implemented via the quota management panel in the project detail header (Sample Target vs Achieved),
plus per-tab progress visibility.

### Risk Status
Displays potential risks including:
- Completion risk: end date within 7 days and < 80% complete (critical) or 14 days / < 50% (warning)
- Back-check rate below target
- High flagged/error rate (> 5% warning, > 10% critical)
- No data uploaded yet
Risk statistics feed from activity tracking numbers and deadlines.

### Aesthetics
- Drill-downs: project detail drill-down with 7 sub-tabs
- Hover effects: all Plotly charts have hover tooltips
- Customizable views: filters on dashboard (status, sort), wave selection in comparison tab

### Wave / Period Comparison
Compare the same project across multiple waves or data collection periods.
Each upload is tagged with an optional wave label (e.g., "Wave 1", "April 2025", "Q2").
The Wave Comparison tab shows:
- Error rate trend: Estimated (rolling baseline) vs Actual vs Variance — line + bar chart
- Back-check rate vs target per wave
- Listen-in rate vs target per wave
- Approved interviews and productivity (interviews/day) per wave
- Average interview duration per wave
- Summary table across all waves

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | **Streamlit** (prototype → server) |
| Data | pandas + openpyxl + xlrd |
| Database | SQLite (prototype); PostgreSQL (production) |
| Auth | Email + password with bcrypt hashing |
| Charts | Plotly Express |
| Export | xlsxwriter (xls) + pyreadstat (SAV/SPSS) |
| Scheduling | APScheduler (twice-weekly refresh) |
| iField | Manual Excel upload for prototype; API hook prepared |

---

## App Folder Structure

```
qc_app/
├── .streamlit/config.toml
├── pages_modules/
│   ├── __init__.py
│   ├── dashboard.py          # All-projects summary, risk alerts, activity feed
│   ├── project_detail.py     # Project drill-down router + quota management header
│   ├── quality_report.py     # QR upload, KPIs, charts, quality queries, mitigation
│   ├── backcheck_report.py   # Back-check upload + viz
│   ├── cancelled_interviews.py
│   ├── performance_report.py
│   ├── timing_report.py
│   ├── listen_in.py          # Manual + batch listen-in tracking
│   ├── wave_comparison.py    # Cross-wave analytics tab
│   └── admin.py              # User, project management, upload history
├── utils/
│   ├── __init__.py
│   ├── charts.py
│   └── exports.py
├── assets/style.css
├── app.py                    # Entry point + routing
├── config.py
├── database.py
├── auth.py
└── requirements.txt
```

---

## User Roles & Permissions

| Role | Manage Users/Projects | Upload Data | Drill-down | View All |
|---|---|---|---|---|
| QC Executive | Yes | Yes | Yes (all) | Yes |
| Operations Manager | Yes | Yes | Yes (all) | Yes |
| QC Officer | No | Yes (assigned) | Yes (assigned) | Summary only |
| Project Manager | No | No | Yes (assigned) | Summary only |
| Researcher | No | No | Yes (assigned) | Summary only |
| Management | No | No | No | Yes (all) |
| Other | No | No | No | Yes (all, no drill-down) |

**Notes:**
- QC Executive creates QC Officers, assigns them to projects
- QC Officers can view ALL projects in the summary dashboard (no drill-down on unassigned)
- Management and Other see the full project list but cannot drill into project detail
- Self-registration creates an "Other" account; role must be elevated by admin

---

## Navigation Structure

```
Dashboard (all roles)
  ├── Risk Alert strip (computed from project metrics)
  ├── Recent Activity feed (latest uploads across projects)
  └── [drill-down → Project Detail] (drilldown roles only, assigned projects)
       ├── Quality Report        (+ Quality Queries + Mitigation sections)
       ├── Back-check Report
       ├── Cancelled Interviews
       ├── Performance Report
       ├── Timing Report
       ├── Listen-in
       └── Wave Comparison       (cross-wave/period analytics)
Admin Panel (qc_executive, operations_manager only)
  ├── User Management
  ├── Project Management (full edit: name, client, targets, dates, status)
  ├── Project Assignments
  └── Upload History
```

---

## Brand Colors (Ipsos)

```css
--navy:   #1F2B6C;   /* headers, sidebar */
--teal:   #00B5AD;   /* accent, progress */
--cyan:   #4FC3F7;   /* secondary */
--yellow: #D4E157;   /* warning */
--orange: #FF7043;   /* critical / risk */
--white:  #FFFFFF;
--gray:   #F5F5F5;   /* card backgrounds */
```

---

## Data Sources & Column Schemas

### 1. Quality Report
**iField export → TOPLINE QUALITY CHECKS sheet**

Required columns in upload template:

| Column Name | Type | Description |
|---|---|---|
| INSTANCE_ID | Text | Unique survey instance ID |
| INTERVIEWER_ID | Text | Interviewer code |
| INTERVIEW_DATE | Date | Date interview was conducted |
| INTERVIEW_START_TIME | Time | Start time |
| INTERVIEW_END_TIME | Time | End time |
| DURATION_MINUTES | Number | Duration in minutes (system) |
| DURATION_FLAG | Text | Okay / Flag |
| STRAIGHT_LINING | Text | 0 = none; flag text if detected |
| LONG_PAUSE | Text | 0 = none; flag text if detected |
| REGION | Text | Geographic region |
| LOCATION | Text | Specific location/county |
| SAMPLE_POINT_ID | Text | Sample point code |
| APPROVAL_STATUS | Text | Approved / Pending / Cancelled |

Optional columns (auto-detected if present):

| Column Name | Type | Description |
|---|---|---|
| GPS_STATUS | Text | Present / Missing / Duplicate |
| PHONE_PRESENT | Text | Yes / No |
| AUDIO_PRESENT | Text | Yes / No |
| DURATION_VALIDATION | Text | HH:MM:SS format |
| QC_COMMENTS | Text | Free text notes |

Auto-mapping from known iField column names is applied on upload.

**KPI derivations:**
- Error rate = flagged records / total records
- Duration avg/min/max per interviewer, region, project
- Straight-lining rate, long pause rate
- GPS issue rate, phone missing rate, audio missing rate

---

### 2. Back-check Report
**iField OM_BackCheckResultReport sheet**

| Column Name | Description |
|---|---|
| BC_INSTANCE_ID | Back-check instance ID |
| ORIGINAL_INSTANCE_ID | Original interview ID |
| INTERVIEW_STATUS | Completed / Pending / etc. |
| REGION | Region |
| LOCATION | Location |
| SAMPLE_POINT_ID | Sample point |
| BACKCHECKER_ID | Back-checker code |
| INTERVIEWER_ID | Original interviewer code |
| SCRIPT_NAME | Project/survey name |
| INTERVIEW_DATE | Date of original interview |
| BACKCHECK_DATE | Date back-check was done |
| ERROR_01 through ERROR_13 | Binary error flags (see below) |

**Error codes:**
1. Totally fraudulent interview
2. Different respondent name/address
3. Mismatched quotas (age, gender)
4. Wrong usership/recruitment criteria
5. Wrong telephone number
6. Unattainable/invalid telephone number
7. Engaged/Answer machine
8. Refused/unable to reach respondent
9. Respondent doesn't remember interview
10. Back-check abandoned/incomplete
11. Interview done on wrong mode (paper/phone instead of CAPI)
12. Voice recording permission issue
13. Respondent already participated recently

**KPIs:**
- Back-check rate = completed / approved interviews (target: 20%)
- Effective rate = interviews with no critical errors / completed back-checks
- Error type distribution (donut chart)

---

### 3. Cancelled Interviews Report
**iField Interview Back Check Report sheet**

Key columns: Instance ID, Region, Location, Sample Point ID, Interviewer ID, Script Name,
Interview Date, Start/End Times, Interview Length (minutes), Active Length, Avg Lengths,
Idle Time, Gap to Last Interview, Same Day Finish, QF A–F (quality flags), 
Interviewer Performance, Back-check Results (Telephone/F2F/Independent)

**KPIs:** Cancellation counts by interviewer/region, gap distribution, quality flag rates

---

### 4. Performance Report
**Project Performance Report sheet**

Key columns: Login (interviewer), Management Region, First/Last Interview,
Interview Completes, Follow-Up Completes, ECS Completes, Work Summary,
Accompaniment, Cancelled Interviews, Back-Check Telephone/F2F Created/Completed

**KPIs:**
- Accompaniment rate (target: 20%)
- Team retention/attrition (interviewers per project)
- Engagement frequency across projects

---

### 5. Timing Report
**TimingReportDataExport sheet**

Key columns: Instance ID, Interviewer ID, Region, Interview Date, Duration (minutes)

**KPIs:** Avg/min/max interview duration per interviewer, region, project

---

## KPI Table (from Write-up Annexure)

| KPI | Description | Chart Type |
|---|---|---|
| Summary Metrics | Overview of all tracked variables | Column / KPI cards |
| Error Types | Straight-lining, inconsistencies, missing GPS, duplicate phones, short gaps | Donut / Stacked bar |
| Error Distribution | Errors crossfiltered by region, interviewer, project | Bar |
| Productivity Trends | Interviewer/region contribution to total interviews per project | Line |
| Risk | Flagged metrics vs targets and deadlines | Pop-up alerts |
| Listen-in Efforts | Listen-in sessions vs target | Donut / Stacked |
| Team Retention & Attrition | Total interviewers/supervisors, engagement frequency across projects | Bar |
| Back-check Efforts | Back-checked interviews vs target | Donut / Stacked |
| Interview Duration | Avg per interviewer, region, project | Line (feasibility of crosstab with productivity) |
| Wave Comparison | Estimated vs Actual error rate and variance across waves | Line + Bar |

---

## Quota Management (Project Detail Header)

Displayed in the project detail banner:
- **Sample Target** — set at project creation
- **Achieved** — count of Approved records from Quality Report uploads
- **+/- overflow** — shown in yellow (over-achieved) or orange (under-achieved)
- **Back-check rate** vs target (✅ or ⚠️)
- **Listen-in rate** vs target (✅ or ⚠️)

---

## Quality Queries & Mitigation (Quality Report Tab)

Auto-generated from upload data:
- Straight-lining / self-administration rate
- Long pauses count
- Duplicate or missing GPS co-ordinates
- Missing telephone numbers
- Missing audio recordings
- LOI < 50% of average (short duration flags)
- Cancelled/invalid interviews

Standard mitigation bullets (always shown):
- Held debrief sessions and checked improvements
- Listened in to audio-recorded interviews
- Accompanied interviewers with major issues
- Telephonic back-checks to affirm interviews
- Queries shared with field coordinator

---

## Dashboard Pages Detail

### Page 1 — Dashboard (All Projects Summary)
- KPI card row: total active projects, total approved interviews, average completion %, open risks
- Bar/column chart: per-project completion vs. target
- Project table: Project Name | Client | Sample Target | Approved | % Complete | Status | Last Updated
- Each project row has "View Details" button → routes to Project Detail (if role permits drill-down)
- Filters: status (Active/Completed/Paused), date range

### Page 2 — Project Detail (Drill-down)
- Project header: name, client, target, dates, status
- Sub-tabs:
  - Quality Report
  - Back-check Report
  - Cancelled Interviews
  - Performance Report
  - Timing Report
- Upload panel per tab (if upload role)

### Page 3 — Quality Report Tab
- Upload section: drag-and-drop Excel, template download button, column mapping UI
- Summary KPI cards: Total Interviews | Approved | Pending | Flagged | Error Rate %
- Duration cards: Avg | Max | Min (in minutes)
- Charts:
  - Donut: Approval status breakdown
  - Stacked bar: Error types (straight-lining, long pause, GPS, phone, audio) per interviewer
  - Bar: Error distribution by region and interviewer (crossfilter)
  - Line: Productivity trend (interviews per day per interviewer)
  - Line: Avg interview duration per interviewer / region
- Filterable data table with export button

### Page 4 — Back-check Report Tab
- Upload section
- KPI cards: Completed Back-checks | Effective | % Rate | Target (20%)
- Donut: Back-check rate (achieved vs. target)
- Donut/Stacked: Error type breakdown
- Bar: Error distribution by interviewer and region
- Data table

### Page 5 — Cancelled Interviews Tab
- Upload section
- KPI cards: Total Cancellations | % of Total Submitted
- Bar: Cancellations by interviewer / region
- Quality flag rate chart (QF A–F)
- Interview gap distribution histogram

### Page 6 — Performance Report Tab
- Upload section
- KPI cards: Total Interviewers | Accompaniment Rate | Avg Completes per Interviewer
- Bar: Interviewers by completes (sorted)
- Donut: Accompaniment achieved vs. target
- Bar: Team retention (interviewers active across multiple projects)
- Data table

### Page 7 — Timing Report Tab
- Upload section
- KPI cards: Avg Duration | Max | Min
- Line: Duration trend per interviewer over time
- Bar: Avg duration per region
- Scatter: Duration vs. productivity (feasibility of crosstab)

### Page 8 — Wave Comparison Tab
- Only shows when at least one upload has been tagged with a wave label
- Error rate trend chart: Estimated (rolling baseline) vs Actual vs Variance per wave
- Back-check rate per wave vs target (bar, colour-coded)
- Listen-in rate per wave vs target
- Productivity and approved interviews per wave (dual-axis bar + line)
- Average duration trend per wave (area line)
- Wave summary table (all metrics in one view)

### Page 9 — Admin Panel
- User Management: list users, add user, edit role, deactivate
- Project Management: add project, edit details, assign users, change status
- Data Management: view upload history, delete bad uploads
- Export: download any dataset as xls or SAV

---

## Access, Updates & Reports

### Access Requirements
- Accessible on **mobile handsets** (insights on the go) and **laptop/desktop**
- Responsive layout; KPI cards and charts must render usably on small screens
- Role-based access control (see User Roles table above)
- Prototype: guest access with full QC Executive permissions (no account required)

### Data Refresh Cadence
- **Automated refresh:** twice a week, overnight (APScheduler)
- **Manual uploads:** any time via the upload panels (QC Officer and above)
- **Update cadence by report type:**
  - Quality Report: monthly or when available from iField
  - Back-check Report: monthly or when available
  - Performance Report: monthly or when available
  - Wave Comparison: per wave/period as data is tagged

### Export Requirements
All data tables and reports are exportable in:
- **Excel (.xlsx)** — primary format for most stakeholders
- **SAV / SPSS (.sav)** — for researchers and DP teams working offline
Export buttons appear on every data tab.

### Import / Data Sources
Priority order for data ingestion:
1. **iField** — primary source; manual Excel export for prototype, API hook prepared for production
2. **SurveyCTO** — secondary; standard CSV/Excel export compatible with same column mapping
3. **Survey Solutions** — tertiary; similar Excel export structure

All sources go through the same normalisation pipeline (`_normalise()` in each module).

---

## Envisaged Statistical Layouts (Write-up Slides 9–11)

These describe the intended visual design of key dashboard sections, including example data
values used to illustrate the layout. Implementation should match these layouts.

### Wave / Period Comparison Chart
Illustrative example (Wave 1 through Wave 4):

| Wave | Total | Approved | Estimated Error | Actual Error | Variance |
|---|---|---|---|---|---|
| Wave 1 | 120 | 108 | 5.0% | 6.7% | +1.7pp |
| Wave 2 | 135 | 124 | 6.7% | 4.8% | −1.9pp |
| Wave 3 | 98  | 90  | 5.8% | 7.8% | +2.0pp |
| Wave 4 | 150 | 141 | 6.4% | 5.0% | −1.4pp |

Estimated = rolling mean of prior waves. Variance bars use orange (+) / teal (−).
Dual y-axis: left = error rate %, right = variance (pp).

### Quota Management Display (Project Detail Header)
```
PROJECT: [Name]                          CLIENT: [Client]
Sample Target:  500    Achieved: 423    -77 (85%)
Back-check:     20%    Actual:   18%    ⚠️ Below target
Listen-in:      10%    Actual:   12%    ✅ On track
```

### Back-checks & Accompaniments Detail Block
Shown in Quality Report / Performance tab:
```
Back-checks Completed:   84 / 423  (19.9%)   Target: 20%  ⚠️
Accompaniments:          47 / 423  (11.1%)   Target: 20%  ⚠️
Telephone back-checks:   62
F2F back-checks:         22
F2F in-field:            14
```
Back-check error breakdown (ERROR_01 – ERROR_13) displayed as donut + detail table.

### Interview Variable Checks (Quality Report Tab — Quality Queries section)
Auto-generated issue list from upload data. For each flagged category:
```
⚠️  Straight-lining detected:     12 instances  (2.8%)
⚠️  Long pauses (> threshold):    7 instances   (1.7%)
⚠️  Missing GPS:                  23 instances  (5.4%)
⚠️  Duplicate GPS:                4 instances   (0.9%)
⚠️  Missing telephone number:     6 instances   (1.4%)
⚠️  Missing audio recording:      9 instances   (2.1%)
⚠️  Short LOI (< 50% avg):        18 instances  (4.3%)
⚠️  Cancelled / invalid:          5 instances
```
Mitigation section follows automatically (standard bullets, always shown).

### Duration Display (Timing Report Tab)
```
Average Duration:   24.3 min    Median: 23.1 min
Maximum:            61 min      Minimum: 8 min
Below 50% avg:      18 interviews flagged  (threshold: 12.2 min)
```
Histogram with avg line and 50%-avg threshold line.
Bar chart: avg duration per interviewer (sorted descending).
Scatter: avg duration vs. interview completes per interviewer (outlier detection).

### Listen-in Rate Display (Listen-in Tab)
```
Approved Interviews:   423
Listen-in Sessions:    51
Listen-in Rate:        12.1%    Target: 10%   ✅
Pass Rate:             88%
```
Gauge chart (rate vs target) + result donut (Pass / Fail / Partial).

---

## Quality Assurance & Data Safety

- All data processed within the dashboard is **confidential** and for internal Ipsos Kenya use only.
- Data is not shared with external parties or stored on public infrastructure.
- The QC process adheres to **ISO 20252:2019** (Market, opinion and social research —
  Vocabulary and service requirements), Ipsos Kenya's operating standard.
- Survey data uploaded to the dashboard is handled in accordance with Ipsos global data
  protection policies and applicable Kenyan data protection legislation.
- Access is role-based; interviewers and field staff do not have dashboard access.
- Prototype uses SQLite (local file); production deployment must use PostgreSQL on a
  secured internal server with encrypted connections (TLS).

---


## Quality Report Column Mapping (iField → Standard)

```python
IFIELD_COLUMN_MAP = {
    "INSTANCE ID": "INSTANCE_ID",
    "Instance ID ": "INSTANCE_ID",
    "INTERVIEWER ID": "INTERVIEWER_ID",
    "Interviewer ID": "INTERVIEWER_ID",
    "INTERVIEW DATE_START": "INTERVIEW_DATE",
    "Interview Date": "INTERVIEW_DATE",
    "INTERVIEW START TIME": "INTERVIEW_START_TIME",
    "Interview Start Time": "INTERVIEW_START_TIME",
    "INTERVIEW END TIME": "INTERVIEW_END_TIME",
    "Interview End Time": "INTERVIEW_END_TIME",
    " DURATION_1_SYSTEM": "DURATION_MINUTES",
    "Interview length": "DURATION_MINUTES",
    "DURATION FLAG": "DURATION_FLAG",
    "STRAIGHT-LINING": "STRAIGHT_LINING",
    "STRAIGHT LINING [From iField]": "STRAIGHT_LINING",
    "LONG PAUSE [From iField]": "LONG_PAUSE",
    "Region": "REGION",
    "Sample Point ID": "SAMPLE_POINT_ID",
    "Location": "LOCATION",
    "Script Name": "PROJECT_NAME",
}
```

---

## Deployment Notes

**Prototype:** Streamlit Community Cloud
- Add `requirements.txt` and push to GitHub
- SQLite DB resets on each redeploy — acceptable for prototype
- Set secrets in Streamlit Cloud dashboard

**Production:** Linux server with gunicorn/nginx or Docker
- Switch DB_PATH to PostgreSQL connection string
- Enable HTTPS
- Configure email SMTP for user notifications (future)

---

## iField API (Future)

Prepare a `data/ifield_connector.py` module with:
- `IFieldClient(base_url, api_key)` class
- `fetch_backcheck_report(project_id, date_from, date_to)` method
- `fetch_quality_report(...)` method
- Feature flag `USE_IFIELD_API=false` — falls back to Excel upload when false


##IMPLEMENT EVERYTHING ABOVE
The system should be able to answer the questions below nad more:
I would like to create a Quality control system using streamlit in python. The system should have a login page. After one log in, I would like them to view the pages according to their roles. I would like to have the default landing page as “Dashboard”, which gives a summary of all Active projects, their sample size and achievements. 
I would like a drill down where one goes to each project and have a project based dashboard.
The project-based dashboard should now have the detailed project progress:
1) Quality report
2) Back-check report.
3) Cancelled Interviews report.
4) Project performance report.
5) Timing Report.

Each of the above has Excel Data, which is to be uploaded by the QC officer or linked directly from the database.

The roles involves: 
1) The QC Executive: Adds QC officers and projects to the system,
2) QC officer: adds project based data to the system, add can only view the projects assigned to them by the QC Executive, they can view all the projects without drill down rights.
3) Project Manager-Have view only rights and can view projects assigned to them by QC Executive:
4)Researcher: Has view only rights and can view projects assigned to them by QC Executive:
5) Operations manager: Has all rights as the QC Executive:
6) Management: Can view only all projects:
7) Others: Can only create a user, login and only view The overall dashboard with no drill down rights.
Write the codes for “Quality report” page, I would like to have specific colums on the data to be uploaded here
Write the codes for “Quality report” page, I would like to have specific colums on the data to be uploaded here
