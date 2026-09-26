"""
Page 3: Interactive Plot.

Requirements:
    - plot with header, axis titles and other relevant formatting
    - st.selectbox choosing any single column, or all columns together
    - st.select_slider to select a subset of the months
      (default: the first month)
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from data_loader import load_data, NUMERIC_COLS

st.title("📈 Interactive Plot")

df = load_data()

# ---------------------------------------------------------------------------
# Sidebar filters.
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

area_types = ["All"] + sorted(df["area_type"].dropna().unique().tolist())
area_type_choice = st.sidebar.selectbox("area_type", area_types)

if area_type_choice != "All":
    area_nrs = (
        ["All"]
        + sorted(
            df.loc[df["area_type"] == area_type_choice, "area_nr"]
            .dropna().unique().astype(int).tolist()
        )
    )
else:
    area_nrs = ["All"] + sorted(df["area_nr"].dropna().unique().astype(int).tolist())

area_nr_choice = st.sidebar.selectbox("area_nr", area_nrs)

mask = df["date"].notna()
if area_type_choice != "All":
    mask &= df["area_type"] == area_type_choice
if area_nr_choice != "All":
    mask &= df["area_nr"] == area_nr_choice

df_f = df.loc[mask].copy()

# ---------------------------------------------------------------------------
# Dropdown: one column or all columns together.
# ---------------------------------------------------------------------------
numeric_cols = [c for c in NUMERIC_COLS if c in df_f.columns]
options = ["All numeric columns"] + numeric_cols
choice = st.selectbox("Select column", options)

# ---------------------------------------------------------------------------
# Month range slider. Default: first month only.
# ---------------------------------------------------------------------------
df_f["month"] = df_f["date"].dt.to_period("M").astype(str)
months = sorted(df_f["month"].dropna().unique().tolist())

if not months:
    st.warning("No data available for the selected filters.")
    st.stop()

month_range = st.select_slider(
    "Select month range",
    options=months,
    value=(months[0], months[0]),   # default: first month
)

start_m, end_m = month_range
subset = df_f[(df_f["month"] >= start_m) & (df_f["month"] <= end_m)]

st.caption(
    f"Showing **{len(subset):,}** rows from **{start_m}** to **{end_m}** "
    f"(area_type = {area_type_choice}, area_nr = {area_nr_choice})."
)

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
if choice == "All numeric columns":
    fig = go.Figure()

    # Left axis: fractions + change × 100
    for col in [c for c in ["fill_ratio", "fill_ratio_prev_week"] if c in subset.columns]:
        fig.add_trace(go.Scatter(
            x=subset["date"], y=subset[col],
            mode="lines", name=col, yaxis="y",
        ))
    if "fill_ratio_change" in subset.columns:
        fig.add_trace(go.Scatter(
            x=subset["date"], y=subset["fill_ratio_change"] * 100,
            mode="lines", name="fill_ratio_change × 100",
            yaxis="y", opacity=0.7,
        ))

    # Right axis: TWh values
    for col in [c for c in ["filled_TWh", "capacity_TWh"] if c in subset.columns]:
        fig.add_trace(go.Scatter(
            x=subset["date"], y=subset[col],
            mode="lines", name=col, yaxis="y2",
        ))

    fig.update_layout(
        title=f"All numeric columns ({start_m} → {end_m})",
        xaxis_title="Date",
        yaxis=dict(title="Fill ratio (0–1), change × 100", side="left"),
        yaxis2=dict(title="Energy (TWh)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
        height=600,
    )
else:
    fig = px.line(
        subset, x="date", y=choice,
        title=f"{choice} ({start_m} → {end_m})",
    )
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=choice,
        hovermode="x unified",
        height=600,
    )

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Small multiples view.
# ---------------------------------------------------------------------------
with st.expander("Show small multiples (one panel per numeric column)"):
    fig_sm = make_subplots(
        rows=len(numeric_cols), cols=1,
        shared_xaxes=True, subplot_titles=numeric_cols,
        vertical_spacing=0.03,
    )
    for i, col in enumerate(numeric_cols, start=1):
        fig_sm.add_trace(
            go.Scatter(
                x=subset["date"], y=subset[col],
                mode="lines", name=col, line=dict(width=0.7),
            ),
            row=i, col=1,
        )
    fig_sm.update_layout(
        height=180 * len(numeric_cols) + 150,
        showlegend=False,
        title_text="Small multiples",
        xaxis_title="Date",
    )
    st.plotly_chart(fig_sm, use_container_width=True)