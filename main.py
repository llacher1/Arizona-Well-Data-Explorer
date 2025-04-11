import streamlit as st
from well_functions import *
from mapping import plot_wells_on_map

import pandas as pd
df = pd.read_parquet("wells_cleaned_main.parquet")
df.columns = df.columns.str.lower().str.strip()
if 'x' not in df.columns and 'dd_long' in df.columns:
    df['x'] = df['dd_long']
if 'y' not in df.columns and 'dd_lat' in df.columns:
    df['y'] = df['dd_lat']

#

# Set Streamlit app title
st.title("Arizona Well Data Explorer")
st.subheader("Data from the GWSI 2024 well dataset")

# Dropdowns for selecting variable of interest and grouping field
value_columns, group_by_columns = get_available_columns()

value_col = st.selectbox("Select a variable to analyze (Z-coordinate):", value_columns)
group_col = st.selectbox("Select a field to group by:", group_by_columns)

# Optional group selection
summary_stats = get_summary_stats(value_col, group_col)
group_options = summary_stats[group_col].dropna().unique()
selected_group = st.selectbox(f"Filter by group in {group_col} (optional):", ["All"] + list(group_options))
if selected_group == "All":
    selected_group = None

# Store selections in session_state so they’re accessible in mapping.py
st.session_state["value_col"] = value_col
st.session_state["group_col"] = group_col
st.session_state["selected_group"] = selected_group

# Show summary statistics table
st.subheader("Summary Statistics")
st.dataframe(summary_stats)

# Show plots
st.subheader("Boxplot")
st.plotly_chart(make_boxplot(value_col, group_col, selected_group), use_container_width=True)

st.subheader("Histogram")
st.plotly_chart(make_histogram(value_col, selected_group, group_col), use_container_width=True)

st.subheader("3D Scatter Plot")
st.plotly_chart(make_scatter_xyz(value_col, selected_group, group_col), use_container_width=True)

# Depth mode toggle for vertical profile
st.subheader("3D View of Well Depths")
depth_mode = st.radio("Choose vertical extent mode:", options=["wl_dtw", "well_depth"])
st.plotly_chart(make_well_vertical_plot(df, selected_group, group_col, depth_mode=depth_mode), use_container_width=True)

# Show map of selected wells
st.subheader("Map of Selected Wells")
df.columns = df.columns.str.lower().str.strip()
if 'x' not in df.columns and 'dd_long' in df.columns:
    df['x'] = df['dd_long']
if 'y' not in df.columns and 'dd_lat' in df.columns:
    df['y'] = df['dd_lat']
if selected_group:
    st.plotly_chart(plot_wells_on_map(df, selected_group, group_col), use_container_width=True)
