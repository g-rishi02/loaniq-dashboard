"""
LoanIQ — Plotly chart builders.
All charts use the dark navy theme matching the app background.
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# Shared layout defaults
_BG      = "rgba(0,0,0,0)"
_PAPER   = "rgba(0,0,0,0)"
_FONT    = dict(family="Inter, sans-serif", color="#94A3B8")
_GRID    = "#1E3A5F"
_MARGIN  = dict(l=10, r=10, t=30, b=10)


def gauge_chart(value: float, title: str, accent: str = "#00D4FF") -> go.Figure:
    """Compact arc gauge for the top metrics row."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 22, "color": "#F1F5F9",
                                         "family": "JetBrains Mono"}},
        title={"text": title, "font": {"size": 10, "color": "#64748B",
                                        "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": _BG,
                     "tickfont": {"color": _BG}},
            "bar":  {"color": accent, "thickness": 0.6},
            "bgcolor": "#0F2340",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "#1E3A5F"},
                {"range": [40, 70], "color": "#1A3050"},
                {"range": [70,100], "color": "#152540"},
            ],
            "threshold": {
                "line": {"color": accent, "width": 3},
                "thickness": 0.8,
                "value": value,
            },
        }
    ))
    fig.update_layout(
        paper_bgcolor=_PAPER, plot_bgcolor=_BG,
        font=_FONT,
        height=150,
        margin=dict(l=10, r=10, t=25, b=5),
    )
    return fig


def probability_dial(prob: float, title: str, accent: str = "#00D4FF") -> go.Figure:
    """Larger dial with colour zones — no delta shown (confuses non-technical users)."""
    pct = prob * 100
    if accent == "#00D4FF":
        bar_color = "#10B981" if pct >= 70 else ("#F59E0B" if pct >= 45 else "#EF4444")
    else:
        bar_color = "#EF4444" if pct >= 50 else ("#F59E0B" if pct >= 20 else "#10B981")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={"suffix": "%", "font": {"size": 36, "color": "#F1F5F9",
                                         "family": "JetBrains Mono, monospace"},
                "valueformat": ".1f"},
        title={"text": title, "font": {"size": 11, "color": "#94A3B8",
                                        "family": "Inter"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#1E3A5F",
                "tickfont": {"size": 9, "color": "#475569"},
                "nticks": 6,
            },
            "bar":  {"color": bar_color, "thickness": 0.55},
            "bgcolor": "#0F2340",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  30], "color": "#0D1F35"},
                {"range": [30, 60], "color": "#0F2340"},
                {"range": [60,100], "color": "#112445"},
            ],
            "threshold": {
                "line": {"color": "#F1F5F9", "width": 2},
                "thickness": 0.75,
                "value": 50,
            },
        }
    ))
    fig.update_layout(
        paper_bgcolor=_PAPER, plot_bgcolor=_BG,
        font=_FONT,
        height=260,
        margin=dict(l=20, r=20, t=40, b=5),
    )
    return fig


def shap_bar_chart(shap_data: dict, label: str, accent: str = "#00D4FF") -> go.Figure:
    """
    Horizontal bar chart of SHAP values for one prediction.
    Positive = pushes toward the positive class.
    Negative = pushes against.
    """
    features = shap_data.get("features", [])
    values   = shap_data.get("values",   [])

    if not features or not values:
        return go.Figure()

    # Sort by absolute impact, keep top 10
    pairs  = sorted(zip(features, values), key=lambda x: abs(x[1]), reverse=True)[:10]
    feats  = [p[0] for p in reversed(pairs)]
    vals   = [p[1] for p in reversed(pairs)]
    colors = ["#10B981" if v > 0 else "#EF4444" for v in vals]

    fig = go.Figure(go.Bar(
        x=vals, y=feats,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:+.3f}" for v in vals],
        textposition="outside",
        textfont=dict(size=10, color="#94A3B8", family="JetBrains Mono"),
        hovertemplate="<b>%{y}</b><br>SHAP: %{x:+.4f}<extra></extra>",
    ))
    fig.add_vline(x=0, line_color="#1E3A5F", line_width=1.5)
    fig.update_layout(
        paper_bgcolor=_PAPER,
        plot_bgcolor=_BG,
        font=_FONT,
        height=300,
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(
            title="SHAP Value",
            gridcolor=_GRID, zerolinecolor=_GRID,
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            tickfont=dict(size=10),
            gridcolor=_BG,
        ),
        bargap=0.25,
    )
    return fig


def segment_radar(profile: dict, segment: str, accent: str = "#00D4FF") -> go.Figure:
    """
    Radar / spider chart showing the borrower segment's normalised feature profile.
    """
    # Use a fixed set of interpretable dimensions
    dims = {
        "FICO Score":    ("fico_avg",          300, 850),
        "Income":        ("annual_inc",         0,   200000),
        "Loan Size":     ("loan_amnt",          0,   40000),
        "DTI (inverted)":("dti",                60,  0),      # invert so low DTI = high score
        "Emp. Length":   ("emp_length_num",     0,   10),
        "Credit Age":    ("credit_account_age", 0,   30),
    }

    labels = []
    values = []
    for name, (key, low, high) in dims.items():
        raw = profile.get(key, (low + high) / 2)
        if high != low:
            norm = (raw - low) / (high - low)
        else:
            norm = 0.5
        labels.append(name)
        values.append(float(np.clip(norm, 0, 1)))

    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    # Convert hex accent to rgba for fill (Plotly rejects 8-digit hex)
    def _hex_to_rgba(hex_color, alpha=0.13):
        h = hex_color.lstrip("#")
        if len(h) == 6:
            r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
            return f"rgba({r},{g},{b},{alpha})"
        return f"rgba(0,212,255,{alpha})"

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor=_hex_to_rgba(accent, 0.13),
        line=dict(color=accent, width=2),
        name=segment,
        hovertemplate="%{theta}: %{r:.2f}<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0F2340",
            radialaxis=dict(
                visible=True, range=[0, 1],
                tickfont=dict(size=8, color="#475569"),
                gridcolor=_GRID,
                linecolor=_GRID,
            ),
            angularaxis=dict(
                tickfont=dict(size=9, color="#94A3B8"),
                gridcolor=_GRID,
                linecolor=_GRID,
            ),
        ),
        paper_bgcolor=_PAPER,
        font=_FONT,
        height=270,
        margin=dict(l=30, r=30, t=20, b=20),
        showlegend=False,
    )
    return fig