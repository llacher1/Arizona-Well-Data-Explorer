import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# Load the cleaned dataset (cached so it's only read once)
df = pd.read_parquet("wells_cleaned_main.parquet")
df.columns = df.columns.str.lower().str.strip()

# Ensure coordinates exist
if 'x' not in df.columns and 'dd_long' in df.columns:
    df['x'] = df['dd_long']
if 'y' not in df.columns and 'dd_lat' in df.columns:
    df['y'] = df['dd_lat']

# Load column descriptions from JSON schema
with open("docs/wells_schema.json", "r") as f:
    schema = json.load(f)

column_labels = {entry["name"].lower(): entry["description"] for entry in schema}

def ensure_coordinates(df):
    """Ensure DataFrame has 'x' and 'y' columns based on 'dd_long' and 'dd_lat'."""
    df.columns = df.columns.str.lower().str.strip()
    if 'x' not in df.columns and 'dd_long' in df.columns:
        df['x'] = df['dd_long']
    if 'y' not in df.columns and 'dd_lat' in df.columns:
        df['y'] = df['dd_lat']
    return df

def get_label(col):
    return column_labels.get(col.lower(), col)

def get_available_columns():
    """Return value (z-coordinate) fields and group-by fields."""
    value_columns = ['well_depth', 'wl_dtw', 'wl_elev']
    group_by_columns = ['unit_name', 'major1', 'major2', 'major3', 'generalize',
                        'rock_name', 'aq_name', 'name_abbr', 'basin_name_1', 'subbasin_name']
    return value_columns, group_by_columns

def get_summary_stats(value_col, group_col):
    """Calculate summary statistics grouped by a category."""
    return df.groupby(group_col)[value_col].describe().reset_index()

def make_boxplot(value_col, group_col, selected_group=None):
    data = df[df[group_col] == selected_group] if selected_group else df
    fig = px.box(data, x=group_col, y=value_col, color=group_col if not selected_group else None, points="outliers")
    fig.update_layout(
        title=f"Boxplot of {get_label(value_col)} by {get_label(group_col)}",
        xaxis_title=get_label(group_col),
        yaxis_title=get_label(value_col),
        yaxis=dict(autorange="reversed")
    )
    return fig

def make_histogram(value_col, selected_group=None, group_col=None):
    data = df[df[group_col] == selected_group] if selected_group and group_col else df
    fig = px.histogram(data, y=value_col, nbins=40)
    fig.update_layout(
        title=f"Depth Distribution of {get_label(value_col)}",
        yaxis_title=get_label(value_col),
        xaxis_title="Count",
        yaxis=dict(autorange="reversed")
    )
    return fig

def make_scatter_xyz(value_col, selected_group=None, group_col=None):
    data = df[df[group_col] == selected_group] if selected_group and group_col else df
    color_col = group_col if not selected_group and group_col else value_col
    fig = px.scatter_3d(data, x='x', y='y', z=value_col, color=color_col,
                        title=f"3D Scatter Plot of {get_label(value_col)}")
    fig.update_layout(
        scene=dict(
            xaxis_title=get_label('longitude'),
            yaxis_title=get_label('latitude'),
            zaxis_title=get_label(value_col)
        )
    )
    fig.update_traces(marker=dict(size=2))
    return fig





def make_well_vertical_plot(df, selected_group=None, group_col=None, depth_mode='wl_dtw'):
    """
    Creates a 3D vertical profile plot of wells, color-coded by well_alt (z_top).

    Parameters:
        df (DataFrame): Must include 'x', 'y', 'well_alt', 'wl_dtw', and optionally 'well_depth'.
        selected_group (str): Optional value to filter `group_col`.
        group_col (str): Column to group/filter on.
        depth_mode (str): 'wl_dtw' (well_alt to water table) or 'well_depth' (water table to well bottom).
    """
    df.columns = df.columns.str.lower().str.strip()
    df = ensure_coordinates(df)

    if selected_group and group_col:
        df[group_col] = df[group_col].str.strip().str.lower()
        selected_group = selected_group.lower()
        df = df[df[group_col] == selected_group]

    if depth_mode == 'wl_dtw':
        df = df.dropna(subset=['x', 'y', 'well_alt', 'wl_dtw'])
        df['z_top'] = df['well_alt']
        df['z_bottom'] = df['well_alt'] - df['wl_dtw']
    elif depth_mode == 'well_depth':
        df = df.dropna(subset=['x', 'y', 'well_alt', 'wl_dtw', 'well_depth'])
        df['z_top'] = df['well_alt'] - df['wl_dtw']
        df['z_bottom'] = df['well_alt'] - df['well_depth']
    else:
        raise ValueError("depth_mode must be 'wl_dtw' or 'well_depth'")

    fig = go.Figure()

    zmin = df['z_top'].min()
    zmax = df['z_top'].max()

    for _, row in df.iterrows():
        fig.add_trace(go.Scatter3d(
            x=[row['x'], row['x']],
            y=[row['y'], row['y']],
            z=[row['z_top'], row['z_bottom']],
            mode='lines+markers',
            line=dict(color=row['z_top'], colorscale='Viridis', cmin=zmin, cmax=zmax, width=4),
            marker=dict(size=2),
            hovertext=f"Well ID: {row.get('well_id', 'N/A')}<br>Elevation: {row['z_top']:.2f} m<br>DTW: {row.get('wl_dtw', 'N/A')}<br>Depth: {row.get('well_depth', 'N/A')}",
            hoverinfo='text',
            showlegend=False
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title='Longitude',
            yaxis_title='Latitude',
            zaxis_title='Elevation (m)',
            zaxis=dict()
        ),
        coloraxis_colorbar=dict(title='Well Elevation (m)'),
        margin=dict(l=0, r=0, b=0, t=30),
        height=600,
        title="Vertical Profile of Wells by Elevation"
    )

    return fig


if __name__ == "__main__":
    value_col = "wl_dtw"
    group_col = "unit_name"

    unique_groups = df[group_col].dropna().unique()
    unique_groups.sort()

    print("Available groups for '{}':".format(group_col))
    for i, group in enumerate(unique_groups):
        print(f"[{i}] {group}")

    idx = int(input("\nEnter the index of the group to visualize: "))
    selected_group = unique_groups[idx]

    print("\nSummary statistics:")
    print(get_summary_stats(value_col, group_col).head())

    print("\nGenerating demo plots for group:", selected_group)
    make_boxplot(value_col, group_col, selected_group).show()
    make_histogram(value_col, selected_group, group_col).show()
    make_scatter_xyz(value_col, selected_group, group_col).show()
    make_well_vertical_plot(df, selected_group, group_col).show()
