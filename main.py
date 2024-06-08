# Import packages
import duckdb
import streamlit as st
from utils import load_from_url
import routing

# Establish a connection to a DuckDB database
conn = duckdb.connect(database='data.duckdb')

# Create a cursor object
cursor = conn.cursor()

# Load nodes and edges data from a URL into the database
nodes, edges = load_from_url(conn)

# Write page title and welcome message
st.set_page_config(page_title="SafePath")
st.write("# Welcome to SafePath!")

# Import and execute the routing module
routing