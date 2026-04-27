import plotly.express as px
import plotly.graph_objects as go
from config import CHART_COLORS, IPSOS_NAVY, IPSOS_TEAL, IPSOS_ORANGE, IPSOS_YELLOW


LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="#F5F5F5",
    font=dict(family="Arial, sans-serif", color="#212121"),
    margin=dict(l=30, r=30, t=50, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)


def donut_chart(values, names, title, colors=None):
    fig = go.Figure(go.Pie(
        values=values,
        labels=names,
        hole=0.55,
        marker_colors=colors or CHART_COLORS,
        textinfo="label+percent",
        insidetextorientation="radial",
    ))
    fig.update_layout(title_text=title, title_x=0.5, **LAYOUT)
    return fig


def bar_chart(df, x, y, color=None, title="", barmode="group", orientation="v"):
    fig = px.bar(df, x=x, y=y, color=color, title=title, barmode=barmode,
                 orientation=orientation, color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**LAYOUT)
    return fig


def stacked_bar(df, x, y, color, title=""):
    fig = px.bar(df, x=x, y=y, color=color, title=title, barmode="stack",
                 color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**LAYOUT)
    return fig


def line_chart(df, x, y, color=None, title=""):
    fig = px.line(df, x=x, y=y, color=color, title=title, markers=True,
                  color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**LAYOUT)
    return fig


def scatter_chart(df, x, y, color=None, title="", size=None):
    fig = px.scatter(df, x=x, y=y, color=color, title=title, size=size,
                     color_discrete_sequence=CHART_COLORS)
    fig.update_layout(**LAYOUT)
    return fig


def histogram(df, x, title="", nbins=20):
    fig = px.histogram(df, x=x, title=title, nbins=nbins,
                       color_discrete_sequence=[IPSOS_TEAL])
    fig.update_layout(**LAYOUT)
    return fig


def gauge_chart(value, target, title, suffix="%"):
    color = IPSOS_TEAL if value >= target * 100 else IPSOS_ORANGE
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        delta={"reference": target * 100, "suffix": suffix},
        number={"suffix": suffix},
        title={"text": title, "font": {"size": 14}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, target * 100 * 0.8], "color": "#FFCDD2"},
                {"range": [target * 100 * 0.8, target * 100], "color": "#FFF9C4"},
                {"range": [target * 100, 100], "color": "#C8E6C9"},
            ],
            "threshold": {
                "line": {"color": IPSOS_NAVY, "width": 3},
                "thickness": 0.8,
                "value": target * 100,
            },
        },
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10),
                      paper_bgcolor="white")
    return fig


def kpi_card(label, value, delta=None, delta_label="", suffix="", color=IPSOS_TEAL):
    delta_html = ""
    if delta is not None:
        arrow = "▲" if delta >= 0 else "▼"
        d_color = "#2E7D32" if delta >= 0 else "#C62828"
        delta_html = f'<div style="color:{d_color};font-size:0.85rem;">{arrow} {abs(delta)}{suffix} {delta_label}</div>'
    return f"""
    <div style="background:white; border-radius:10px; padding:1.2rem 1rem;
                box-shadow:0 2px 8px rgba(0,0,0,0.08); border-top:4px solid {color};
                text-align:center; min-height:110px;">
        <div style="color:#666; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;">{label}</div>
        <div style="color:#1F2B6C; font-size:2rem; font-weight:700; margin:0.3rem 0;">{value}{suffix}</div>
        {delta_html}
    </div>"""
