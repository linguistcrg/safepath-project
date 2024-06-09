import streamlit as st
import duckdb
import folium
from folium.plugins import Geocoder
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
from utils import load_from_url, shortest_path, find_closest_point, create_feedback_table

# Connect to DuckDB database
conn = duckdb.connect(database='data.duckdb')
cursor = conn.cursor()
create_feedback_table(conn)

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
m = folium.Map(location=[52.3676, 4.9041], zoom_start=13)
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

if source is not None and destination is not None:
    folium.Marker(
        location=[source[2], source[1]],
        popup="Start",
        tooltip="Start",
        icon=folium.Icon(color="red")
    ).add_to(m)
    
    folium.Marker(
        location=[destination[2], destination[1]],
        popup="End",
        tooltip="End",
        icon=folium.Icon(color="green")
    ).add_to(m)

    # Calculate the shortest path between source and destination
    path = shortest_path(conn, source[0], destination[0])

    if path is not None:
        path_nodes, _ = path
        nodes_query = (f"SELECT id, ST_X(geom) AS longitude, ST_Y(geom) AS latitude FROM ams_walk_nodes WHERE id IN "
                       f"({','.join(map(str, path_nodes))})")
        nodes_data = conn.execute(nodes_query).fetchall()
        nodes_data = {x[0]: x for x in nodes_data}

        # Add nodes as markers
        for node_id in path_nodes[1:len(nodes_data) - 1]:
            node = nodes_data[node_id]
            folium.Marker(
                location=[node[2], node[1]],
                popup=f"Node {node[0]}",
                tooltip=f"Node {node[0]}"
            ).add_to(m)

        # Add edges as polylines and display feedback averages
        total_safety, total_lighting, total_speed, total_overall, edge_count = 0, 0, 0, 0, 0

        for i in range(len(path_nodes) - 1):
            nodeid1 = path_nodes[i]
            nodeid2 = path_nodes[i + 1]

            # Query to get the average ratings for the edge between nodeid1 and nodeid2
            feedback_query = f"""
                SELECT 
                    AVG(safety_rating) AS avg_safety,
                    AVG(lighting_rating) AS avg_lighting,
                    AVG(speed_rating) AS avg_speed,
                    AVG(overall_rating) AS avg_overall
                FROM feedback
                WHERE 
                    (nodeOne = {nodeid1} AND nodeTwo = {nodeid2})
                    OR (nodeOne = {nodeid2} AND nodeTwo = {nodeid1});
            """

            feedback_data = conn.execute(feedback_query).fetchone()

            # Handle None values
            avg_safety = feedback_data[0] if feedback_data[0] is not None else 0.0
            avg_lighting = feedback_data[1] if feedback_data[1] is not None else 0.0
            avg_speed = feedback_data[2] if feedback_data[2] is not None else 0.0
            avg_overall = feedback_data[3] if feedback_data[3] is not None else 0.0

            # Sum up the averages for each edge
            total_safety += avg_safety
            total_lighting += avg_lighting
            total_speed += avg_speed
            total_overall += avg_overall
            edge_count += 1

            # Add polyline with feedback info as popup
            popup_content = f"Safety: {avg_safety:.2f}, Lighting: {avg_lighting:.2f}, Speed: {avg_speed:.2f}, Overall: {avg_overall:.2f}"
            folium.PolyLine(
                locations=[
                    [nodes_data[path_nodes[i]][2], nodes_data[path_nodes[i]][1]],
                    [nodes_data[path_nodes[i + 1]][2], nodes_data[path_nodes[i + 1]][1]]
                ],
                color="blue",
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(m)

        # Calculate the average ratings across the entire path
        if edge_count > 0:
            avg_safety = total_safety / edge_count
            avg_lighting = total_lighting / edge_count
            avg_speed = total_speed / edge_count
            avg_overall = total_overall / edge_count

            st.write("### Average Ratings for the Selected Route")
            # Define function to create progress bars
            def create_progress_bar(label, value):
                bar = f"<progress value='{value * 20}' max='100' style='width: 150px'></progress>"
                return f"{label}: {bar} {value:.2f}/5.00"

            # Create progress bars for each rating
            st.markdown(create_progress_bar("Average Safety Rating", avg_safety), unsafe_allow_html=True)
            st.markdown(create_progress_bar("Average Lighting Rating", avg_lighting), unsafe_allow_html=True)
            st.markdown(create_progress_bar("Average Speed Rating", avg_speed), unsafe_allow_html=True)
            st.markdown(create_progress_bar("Average Overall Rating", avg_overall), unsafe_allow_html=True)
        else:
            st.write("No feedback data available for this route.")

st_folium(m, width=700, height=500)

# Close the database connection
conn.close()
