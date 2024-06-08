import os
import streamlit as st
import duckdb
import folium


from streamlit_folium import st_folium
from loaders import load_from_url



conn = duckdb.connect(database='data.duckdb')

cursor = conn.cursor()

nodes, edges = load_from_url(conn)

conn.close()


st.write("Choose one of the options below")


m1 = folium.Map(location=[52.3676, 4.9041], zoom_start=12)
m2 = folium.Map(location=[52.3678, 4.9041], zoom_start=11)

# Add markers to the map
for row in nodes[:10]:
    folium.Marker(
        location=[row[2], row[1]],
        popup=row[0]
    ).add_to(m1)

for row in nodes[:10]:
    folium.Marker(
        location=[row[2], row[1]],
        popup=row[0]
    ).add_to(m2)
# Create two columns for layout
col1, col2 = st.columns(2)

# Display the first map in the first column
with col1:
    st.header("Route 1")
    st_folium(m1, width=400, height=400)
    st.write("Safety rating: ")
    st.write("Time: ")

# Display the second map in the second column
with col2:
    st.header("Route 2")
    st_folium(m2, width=400, height=400)
    st.write("Safety rating: ")
    st.write("Time: ")

if __name__ == "__routing__":
    routing()