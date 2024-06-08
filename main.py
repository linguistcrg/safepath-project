from ast import main
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

# st.set_page_config(
#     page_title="Hello",
#     page_icon="👋",
# )

st.write("# Welcome to SafePath!")
st.write("The calculator of the safest routes  in Amsterdam for women")

col1, col2 = st.columns(2)

# Create two text input fields side by side
with col1:
    user_input1 = st.text_input("Starting point:")

with col2:
    user_input2 = st.text_input("End point:")

st.sidebar.success("The calculator of the safest routes  in Amsterdam for women")
m = folium.Map(location=[52.3676, 4.9041], zoom_start=12)


for row in nodes[:10]:
    folium.Marker(
        location=[row[2], row[1]],
        popup=row[0]
    ).add_to(m)

# Display the map in Streamlit
st_folium(m, width=700, height=500)

 # Button to navigate to Routing Page
if st.button("Submit"):
        st.experimental_set_query_params(page="routing")
        st.experimental_rerun()

if __name__ == "__main__":
    main()







