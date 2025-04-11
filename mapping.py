import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import streamlit as st
from well_functions import ensure_coordinates

# Load Arizona boundary for default extent
az_boundary = gpd.read_file("shapefiles/AZ_State_Bound.shp").to_crs(epsg=4326)

def plot_wells_on_map(df, selected_group=None, group_col=None):
    """Create a map plot of selected wells over the Arizona boundary using MapLibre."""
    df = ensure_coordinates(df)
    if selected_group and group_col:
        df[group_col] = df[group_col].str.strip().str.lower()
        selected_group = selected_group.lower()
        df = df[df[group_col] == selected_group]
        print(f"{len(df)} wells found for group '{selected_group}'")

    gdf_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['x'], df['y']), crs='EPSG:4326')

    fig = go.Figure()

    # Plot Arizona boundary
    for _, geom in az_boundary.iterrows():
        if geom.geometry.geom_type == 'Polygon':
            x, y = geom.geometry.exterior.xy
            fig.add_trace(go.Scattermap(
                lat=list(y),
                lon=list(x),
                mode="lines",
                line=dict(width=1, color="black"),
                name="AZ Boundary"
            ))

    # Add well points
    fig.add_trace(go.Scattermap(
        lat=gdf_points.geometry.y,
        lon=gdf_points.geometry.x,
        mode='markers',
        marker=dict(size=5, color='red'),
        name='Wells'))

    fig.update_layout(
        map_style="carto-positron",
        map_zoom=5,
        map_center={"lat": 34.0, "lon": -111.5},
        margin={"r":0,"t":0,"l":0,"b":0}
    )

    return fig

if __name__ == "__main__":
    df = pd.read_parquet("wells_cleaned_main.parquet")
    df.columns = df.columns.str.lower().str.strip()
    if 'x' not in df.columns and 'dd_long' in df.columns:
        df['x'] = df['dd_long']
    if 'y' not in df.columns and 'dd_lat' in df.columns:
        df['y'] = df['dd_lat']

    value_col = "wl_dtw"
    group_col = "unit_name"
    selected_group = 'Cretaceous sedimentary rocks'

    print(f"Demo: Mapping wells for group '{selected_group}' by attribute '{group_col}'\n")
    print(df[group_col].unique())
    fig = plot_wells_on_map(df, selected_group, group_col)
    fig.show()

# Streamlit integration
if __name__ != "__main__":
    st.subheader("Map of Selected Wells")
    df = pd.read_parquet("wells_cleaned_main.parquet")
    df.columns = df.columns.str.lower().str.strip()
    if 'x' not in df.columns and 'dd_long' in df.columns:
        df['x'] = df['dd_long']
    if 'y' not in df.columns and 'dd_lat' in df.columns:
        df['y'] = df['dd_lat']

    value_col = st.session_state.get("value_col", "wl_dtw")
    group_col = st.session_state.get("group_col", "unit_name")
    selected_group = st.session_state.get("selected_group", None)

    if selected_group and selected_group != "All":
        st.plotly_chart(plot_wells_on_map(df, selected_group, group_col), use_container_width=True)