# Import packages
import streamlit as st
from streamlit_star_rating import st_star_rating

# Write page title and message
st.set_page_config(page_title="Feedback")
st.write("# We value your feedback!")
st.markdown(
    """
    Please help us improve SafePath by sharing your experience with your suggested route.
    You can rate different aspects of your route and leave a review below:
    """
)


import duckdb
import folium
from folium.plugins import Geocoder
from geopy.geocoders import Nominatim

from streamlit_folium import st_folium

from utils import load_from_url, shortest_path, find_closest_point

conn = duckdb.connect(database='data.duckdb')

cursor = conn.cursor()

nodes, edges = load_from_url(conn)

col1, col2 = st.columns(2)
# Rating input
safety_rating = st_star_rating(label="Feeling of safety", maxValue=5, defaultValue=3, key="easiness_rating", emoticons=True)
lighting_rating = st_star_rating(label="Number of street lights", maxValue=5, defaultValue=3, key="lighting_rating", emoticons=True)
speed_rating = st_star_rating(label="Travel time", maxValue=5, defaultValue=3, key="speed_rating", emoticons=True)
overall_rating = st_star_rating(label="Overall experience", maxValue=5, defaultValue=3, key="overall_rating", emoticons=True)

# Review input
review = st.text_area("Write your review here:")

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

print(source, destination)
if source is not None and destination is not None:
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
        
        if st.button("Submit"):
            st.write("Thank you for your feedback!")
            st.write(f"Feeling of safety: {safety_rating}")
            st.write(f"Number of street lights: {lighting_rating}")
            st.write(f"Travel time: {speed_rating}")
            st.write(f"Overall experience: {overall_rating}")
            st.write(f"Review: {review}") 
            for i in range(len(nodes_data) - 1):
                conn.execute(
                    "INSERT INTO feedback (nodeOne, nodeTwo, safety_rating, lighting_rating, speed_rating, overall_rating, review) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [nodes_data[i][0], nodes_data[i+1][0], safety_rating, lighting_rating, speed_rating, overall_rating, review]
                )
                
            # Retrieve and display the latest feedback
            feedback_data = conn.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT 1").fetchall()
            st.write("Latest Feedback Entry:")
            st.write(feedback_data)

conn.close()

