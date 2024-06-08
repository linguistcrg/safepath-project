import duckdb
import streamlit as st

from utils import load_from_url
import routing

conn = duckdb.connect(database='data.duckdb')

cursor = conn.cursor()

nodes, edges = load_from_url(conn)

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to SafePath!")

routing
