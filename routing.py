
import streamlit as st
import duckdb
import folium
from folium.plugins import Geocoder


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
st.write("The calculator of the safest routes  in Amsterdam for women")

col1, col2 = st.columns(2)

# Create two text input fields side by side
with col1:
    user_input1 = st.text_input("Starting point:")

with col2:
    user_input2 = st.text_input("End point:")
if 'clicked_points' not in st.session_state:
    st.session_state.clicked_points = []


m = folium.Map(location=[52.3676, 4.9041], zoom_start=12)
Geocoder().add_to(m)

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
m.add_child(folium.LatLngPopup())

map_data = st_folium(m, height=500, width=500)
if map_data['last_clicked'] is not None:
    lat = map_data['last_clicked']['lat']
    lng = map_data['last_clicked']['lng']
    new_point = {'lat': lat, 'lng': lng}
    
    # Append new point to the session state
    if new_point not in st.session_state.clicked_points:
        st.session_state.clicked_points.append(new_point)

# Display the clicked points
if st.session_state.clicked_points:
    if(len(st.session_state.clicked_points)>=2):
        st.write("Clicked points:")
        point1=st.session_state.clicked_points[0]
        point2=st.session_state.clicked_points[1]
        print(point1)
        print(point2)
        st.write(f"Latitude point 1: {point1['lat']}, Longitude point 1: {point1['lng']}")
        st.write(f"Latitude point 2: {point2['lat']}, Longitude point 2: {point2['lng']}")
conn.close()


# if st.button("Submit"):
#         # Set query parameter to indicate navigation to feedback page
#         st.experimental_set_query_params(page="feedback")
#         # Rerun the app to navigate to the feedback page
#         st.experimental_rerun()


app_path = 'http://localhost:8501'
page_file_path = 'pages/feedback.py'
page = page_file_path.split('/')[1][0:-3]  # get "page1"
st.markdown(
    f'''<a href="{app_path}/{page}" target="_self">Give a feedback</a>''',
    unsafe_allow_html=True
)
