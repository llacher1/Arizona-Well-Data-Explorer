import streamlit as st

# ✅ MUST be the first Streamlit command
st.set_page_config(
    page_title="Arizona Well Data Explorer",
    page_icon=":material/water_drop:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Optional custom CSS (can follow after)
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

from well_functions import *
from mapping import plot_wells_on_map
from mapping import render_map_ui
import pandas as pd



# Load data
df = pd.read_parquet("wells_cleaned_main.parquet")
df = ensure_coordinates(df)



# Set Streamlit app title

st.markdown("""
# Arizona Well Data Explorer 💧

Welcome to the interactive groundwater data explorer for Arizona. This app utilizes data from the 2024 GWSI well database.

This app allows you to:
- Visualize groundwater well depths and water level elevations.
- Explore well characteristics by region, aquifer, and geology.
- Overlay hydrologic features like **Subbasins**, **AMAs**, and **Major Aquifers**.

Use the dropdowns to filter wells, and view 3D depth profiles and geographic maps.

> Created by Ryan Lima (ryan.lima@nau.edu) as part of the Arizona Tri-University Recharge Project
---
""")


# Dropdowns for selecting variable of interest and grouping field
value_columns, group_by_columns = get_available_columns()

#value_col = st.selectbox("Select a variable to analyze (Z-coordinate):", value_columns)
#group_col = st.selectbox("Select a field to group by:", group_by_columns)

# Reverse mapping for selectbox display and retrieval
label_to_col = {get_label(c): c for c in value_columns}
label_to_group_col = {get_label(c): c for c in group_by_columns}

# Streamlit interface
value_col_label = st.selectbox("Select a variable to analyze (Z-coordinate):", list(label_to_col.keys()))
group_col_label = st.selectbox("Select a field to group by:", list(label_to_group_col.keys()))

# Retrieve actual column names
value_col = label_to_col[value_col_label]
group_col = label_to_group_col[group_col_label]

# Optional group selection
summary_stats = get_summary_stats(value_col, group_col)
group_options = summary_stats[group_col].dropna().unique()
selected_group = st.selectbox(f"Filter by group in {group_col} (optional):", ["All"] + list(group_options))
if selected_group == "All":
    selected_group = None

# Filter the dataframe
if selected_group and group_col:
    filtered_df = df[df[group_col].str.strip().str.lower() == selected_group.lower()]
else:
    filtered_df = df.copy()


# Store selections in session_state so they’re accessible in mapping.py
st.session_state["value_col"] = value_col
st.session_state["group_col"] = group_col
st.session_state["selected_group"] = selected_group

# Show summary statistics table
st.subheader("Summary Statistics")
st.dataframe(summary_stats)

# Show plots
st.subheader("Boxplot")
#st.plotly_chart(make_boxplot(value_col, group_col, selected_group), use_container_width=True)
st.plotly_chart(make_boxplot(value_col, group_col, selected_group), use_container_width=True, key="boxplot")

st.subheader("Histogram")
#st.plotly_chart(make_histogram(value_col, selected_group, group_col), use_container_width=True)
st.plotly_chart(make_histogram(value_col, selected_group, group_col), use_container_width=True, key="histogram")


st.subheader("3D Scatter Plot")
#st.plotly_chart(make_scatter_xyz(value_col, selected_group, group_col), use_container_width=True)
st.plotly_chart(make_scatter_xyz(value_col, selected_group, group_col), use_container_width=True, key="scatter_xyz")

# Load metadata
metadata = pd.read_parquet("wells_metadata.parquet")

file_safe_group = selected_group.replace(" ", "_").lower()
file_name = f"filtered_wells_{file_safe_group}.csv"

# Show these sections only if a group has been selected
if selected_group:
    file_safe_group = selected_group.replace(" ", "_").lower()
else:
    file_safe_group = "all"

file_name = f"filtered_wells_{file_safe_group}.csv"

if selected_group:
    # 3D well depth profile
    st.subheader("3D View of Well Depths")
    depth_mode = st.radio("Choose vertical extent mode:", options=["wl_dtw", "well_depth"])
    fig = make_well_vertical_plot(
        df,
        metadata=metadata,
        selected_group=selected_group,
        group_col=group_col,
        depth_mode=depth_mode
    )
    st.plotly_chart(fig, use_container_width=True, key="well_vertical_profile")

    # Map of wells
    render_map_ui(df, selected_group, group_col)

    # ✅ Download section

    csv = filtered_df.to_csv(index=False).encode('utf-8')

    st.markdown("### Download Filtered Data")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=file_name,
        mime='text/csv'
    )
    st.caption("Download the wells currently selected by the filters above as a CSV file.")