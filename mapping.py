import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import streamlit as st
from well_functions import ensure_coordinates

# Load Arizona boundary for default extent
az_boundary = gpd.read_file("shapefiles/AZ_State_Bound.shp").to_crs(epsg=4326)

def plot_wells_on_map(df, selected_group=None, group_col=None, show_subbasin=False, show_amas=False, show_aquifers=False):
    """Create a map of wells with optional overlays for subbasins, AMAs/INAs, and aquifers."""

    df = ensure_coordinates(df)
    if selected_group and group_col:
        df[group_col] = df[group_col].str.strip().str.lower()
        selected_group = selected_group.lower()
        df = df[df[group_col] == selected_group]

    gdf_points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['x'], df['y']), crs='EPSG:4326')
    fig = go.Figure()

    # Plot Arizona boundary
    for _, geom in az_boundary.iterrows():
        if geom.geometry and geom.geometry.geom_type == 'Polygon':
            x, y = geom.geometry.exterior.xy
            fig.add_trace(go.Scattermapbox(
                lat=list(y), lon=list(x),
                mode="lines", line=dict(width=1, color="black"),
                name="AZ Boundary"
            ))

    # Optional shapefile overlays
    if show_subbasin:
        gdf = gpd.read_file("shapefiles/ADWR Groundwater Subbasin.shp").to_crs("EPSG:4326")
        gdf.columns = gdf.columns.str.strip().str.lower()
        print(gdf.columns.tolist())
        display_col = 'subbasin_n'

        unique_names = gdf[display_col].dropna().unique()
        name_map = {name.strip().lower(): name for name in unique_names}
        color_map = dict(zip(name_map.keys(), px.colors.qualitative.Set3[:len(name_map)]))

        for name_norm, name in name_map.items():
            sub_df = gdf[gdf[display_col].str.strip().str.lower() == name_norm]
            for _, row in sub_df.iterrows():
                geom = row["geometry"]
                if geom:
                    if geom.geom_type == 'Polygon':
                        polys = [geom]
                    elif geom.geom_type == 'MultiPolygon':
                        polys = list(geom.geoms)
                    else:
                        continue

                    for poly in polys:
                        x, y = poly.exterior.xy
                        fig.add_trace(go.Scattermapbox(
                            lat=list(y), lon=list(x),
                            mode="lines",
                            fill="toself",
                            line=dict(width=1, color=color_map.get(name_norm, "#999999")),
                            name=name,
                            showlegend=True
                        ))

    if show_amas:
        gdf = gpd.read_file("shapefiles/AMAs_and_INAs.shp").to_crs("EPSG:4326")
        gdf.columns = gdf.columns.str.strip().str.lower()
        print(gdf.columns.tolist())
        display_col = 'basin_name'

        unique_names = gdf[display_col].dropna().unique()
        name_map = {name.strip().lower(): name for name in unique_names}
        color_map = dict(zip(name_map.keys(), px.colors.qualitative.Set3[:len(name_map)]))

        for name_norm, name in name_map.items():
            sub_df = gdf[gdf[display_col].str.strip().str.lower() == name_norm]
            for _, row in sub_df.iterrows():
                geom = row["geometry"]
                if geom:
                    if geom.geom_type == 'Polygon':
                        polys = [geom]
                    elif geom.geom_type == 'MultiPolygon':
                        polys = list(geom.geoms)
                    else:
                        continue

                    for poly in polys:
                        x, y = poly.exterior.xy
                        fig.add_trace(go.Scattermapbox(
                            lat=list(y), lon=list(x),
                            mode="lines",
                            fill="toself",
                            line=dict(width=1, color=color_map.get(name_norm, "#999999")),
                            name=name,
                            showlegend=True
                        ))

    if show_aquifers:
        gdf = gpd.read_file("shapefiles/Major_Aquifers.shp").to_crs("EPSG:4326")
        gdf.columns = gdf.columns.str.strip().str.lower()
        print(gdf.columns.tolist())
        display_col = 'aq_name'

        unique_names = gdf[display_col].dropna().unique()
        name_map = {name.strip().lower(): name for name in unique_names}
        color_map = dict(zip(name_map.keys(), px.colors.qualitative.Set3[:len(name_map)]))

        for name_norm, name in name_map.items():
            sub_df = gdf[gdf[display_col].str.strip().str.lower() == name_norm]

            legend_added = False  # ✅ only once per name_norm

            for _, row in sub_df.iterrows():
                geom = row["geometry"]
                if geom:
                    if geom.geom_type == 'Polygon':
                        polys = [geom]
                    elif geom.geom_type == 'MultiPolygon':
                        polys = list(geom.geoms)
                    else:
                        continue

                    for poly in polys:
                        x, y = poly.exterior.xy
                        fig.add_trace(go.Scattermapbox(
                            lat=list(y), lon=list(x),
                            mode="lines",
                            fill="toself",
                            line=dict(width=1, color=color_map.get(name_norm, "#999999")),
                            name=name,
                            showlegend=not legend_added
                        ))
                        legend_added = True  # ✅ toggled after first plot

    # Add well points
    fig.add_trace(go.Scattermapbox(
        lat=gdf_points.geometry.y,
        lon=gdf_points.geometry.x,
        mode='markers',
        marker=dict(size=5, color='red'),
        name='Wells'))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=5,
        mapbox_center={"lat": 34.0, "lon": -111.5},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=600
    )

    return fig


def render_map_ui(df, selected_group, group_col):
    """Streamlit UI wrapper for map generation with layer toggles."""
    st.subheader("Map of Selected Wells")

    col1, col2, col3 = st.columns(3)
    with col1:
        show_subbasin = st.checkbox("Show Subbasins", value=True)
    with col2:
        show_amas = st.checkbox("Show AMAs & INAs", value=True)
    with col3:
        show_aquifers = st.checkbox("Show Aquifers", value=False)

    fig = plot_wells_on_map(df, selected_group, group_col,
                            show_subbasin=show_subbasin,
                            show_amas=show_amas,
                            show_aquifers=show_aquifers)

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    # Load each shapefile and print column names
    print("\n🧪 Subbasins:")
    gdf = gpd.read_file("shapefiles/ADWR Groundwater Subbasin.shp")
    print(gdf.columns.tolist())

    print("\n🧪 AMAs and INAs:")
    gdf = gpd.read_file("shapefiles/AMAs_and_INAs.shp")
    print(gdf.columns.tolist())

    print("\n🧪 Major Aquifers:")
    gdf = gpd.read_file("shapefiles/Major_Aquifers.shp")
    print(gdf.columns.tolist())
