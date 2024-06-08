import os
import streamlit as st
import duckdb
import folium

from streamlit_folium import st_folium

from loaders import load_from_url, load_local


conn = duckdb.connect()

cursor = conn.cursor()

if os.path.exists("data/nodes.csv"):
    nodes, edges = load_local(conn)
else:
    nodes, edges = load_from_url(conn)

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to Streamlit! 👋")

st.sidebar.success("Select a demo above.")

st.markdown(
    """
    Streamlit is an open-source app framework built specifically for
    Machine Learning and Data Science projects.
    **👈 Select a demo from the sidebar** to see some examples
    of what Streamlit can do!
    ### Want to learn more?
    - Check out [streamlit.io](https://streamlit.io)
    - Jump into our [documentation](https://docs.streamlit.io)
    - Ask a question in our [community
        forums](https://discuss.streamlit.io)
    ### See more complex demos
    - Use a neural net to [analyze the Udacity Self-driving Car Image
        Dataset](https://github.com/streamlit/demo-self-driving)
    - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
"""
)

m = folium.Map(location=[52.3676, 4.9041], zoom_start=12)


for row in nodes:
    folium.Marker(
        location=[row[1], row[2]],  # Adjust based on your CSV structure
        popup=row[0]  # Adjust based on your CSV structure
    ).add_to(m)

# Display the map in Streamlit
st_folium(m, width=700, height=500)
