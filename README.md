# SafePath

## About
“SafePath” is a website application designed to enhance personal safety for women in Amsterdam by providing safer, community-reviewed walking routes. Users can choose routes based on safety, walking time or both. Real-time feedback is continuously used to improve the algorithm that generates routes.

## Tools
We used DuckDB for storing and querying safety data in SQL format. We also used the following datasets: 
- Amsterdam Pedestrian Road Network: Nodes and Edges
- Amsterdam Wijken: Districts
- Amsterdam Safety Statistics (synthetic data)

## Installation
Before using the code, make sure you have the following prerequisites installed:

```
duckdb==1.0.0
folium==0.16.0
st-star-rating==0.0.6
streamlit==1.35.0
streamlit_folium==0.20.0
```

## Acknowledgements
This app was developed for The DuckDB Challenge at Hack4her 2024; a student, women-centered hackaton celebrated from 7 to 9 June 2024 at Vrije Universiteit Amsterdam.
