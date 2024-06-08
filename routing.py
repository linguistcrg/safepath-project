# Import packages
import streamlit as st
import duckdb
import folium
from folium.plugins import Geocoder
from geopy.geocoders import Nominatim

from streamlit_folium import st_folium

from utils import load_from_url, shortest_path, find_closest_point

# Connect to DuckDB database
conn = duckdb.connect(database='data.duckdb')

# Create a cursor object
cursor = conn.cursor()

# Load nodes and edges from the database
nodes, edges = load_from_url(conn)

# Set the page configuration for the Streamlit app
st.set_page_config(page_title="SafePath")

# Display the title and description
st.write("# Welcome to SafePath!")
st.write("The calculator of the safest routes for women in Amsterdam.")

# Create two columns for user input
col1, col2 = st.columns(2)

# Initialise the Amsterdam map
m = folium.Map(location=[52.3676, 4.9041], zoom_start=12)
Geocoder().add_to(m)
geolocator = Nominatim(user_agent="SafePath")

# Initialise source and destination variables
source, destination = None, None

# User input for the starting point
with col1:
    user_input1 = st.text_input("Starting point:")
    if user_input1:
        location = geolocator.geocode(user_input1)
        source = find_closest_point(conn, location.longitude, location.latitude)

# User input for the end point
with col2:
    user_input2 = st.text_input("End point:")
    if user_input2:
        location = geolocator.geocode(user_input2)
        destination = find_closest_point(conn, location.longitude, location.latitude)

print(source, destination)
if source is not None and destination is not None:
    folium.Marker(
        location=[source[2], source[1]],
        popup=f"Start",
        tooltip=f"Start",
        color="red"
    ).add_to(m)

    folium.Marker(
        location=[destination[2], destination[1]],
        popup=f"End",
        tooltip=f"End",
        color="green"
    ).add_to(m)

    # Calculate the shortest path between source and destination
    path = shortest_path(conn, source[0], destination[0])
    with col1:
        st.write("")
    with col2:
        st.write("")

    if path is not None:
        path_nodes, _ = path
        nodes_query = (f"SELECT id, ST_X(geom) AS longitude, ST_Y(geom) AS latitude FROM ams_walk_nodes WHERE id IN "
                       f"({','.join(map(str, path_nodes))})")
        nodes_data = conn.execute(nodes_query).fetchall()

        # Add nodes as markers
        for node in nodes_data:
            folium.Marker(
                location=[node[2], node[1]],
                popup=f"Node {node[0]}",
                tooltip=f"Node {node[0]}"
            ).add_to(m)

        # Add edges as polylines
        for i in range(len(nodes_data) - 1):
            folium.PolyLine(
                locations=[
                    [nodes_data[i][2], nodes_data[i][1]],
                    [nodes_data[i + 1][2], nodes_data[i + 1][1]]
                ],
                color="blue"
            ).add_to(m)

# Display the map in Streamlit
st_folium(m, width=700, height=500)

# Close the database connection
conn.close()
