import os
import streamlit as st
import duckdb
import folium


from streamlit_folium import st_folium

from utils import load_from_url, shortest_path

conn = duckdb.connect(database='data.duckdb')

cursor = conn.cursor()

nodes, edges = load_from_url(conn)

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to SafePath!")

col1, col2 = st.columns(2)

# Create two text input fields side by side
with col1:
    user_input1 = st.text_input("Starting point:")

with col2:
    user_input2 = st.text_input("End point:")

# st.sidebar.success("The calculator of the safest routes  in Amsterdam for women")

# st.markdown(
#     """
#     Streamlit is an open-source app framework built specifically for
#     Machine Learning and Data Science projects.
#     **👈 Select a demo from the sidebar** to see some examples
#     of what Streamlit can do!
#     ### Want to learn more?
#     - Check out [streamlit.io](https://streamlit.io)
#     - Jump into our [documentation](https://docs.streamlit.io)
#     - Ask a question in our [community
#         forums](https://discuss.streamlit.io)
#     ### See more complex demos
#     - Use a neural net to [analyze the Udacity Self-driving Car Image
#         Dataset](https://github.com/streamlit/demo-self-driving)
#     - Explore a [New York City rideshare dataset](https://github.com/streamlit/demo-uber-nyc-pickups)
# """
# )

m = folium.Map(location=[52.3676, 4.9041], zoom_start=12)
path = shortest_path(conn, nodes[0][0], 4859)

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

conn.close()
