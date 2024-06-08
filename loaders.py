import os


def decode_if_bytes(data):
    if isinstance(data, (bytes, bytearray)):
        return data.decode('utf-8')
    return data


def load_from_url(conn):
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    conn.install_extension("httpfs")
    conn.load_extension("httpfs")

    conn.execute("""
        CREATE TABLE ams_walk_nodes AS SELECT * FROM st_read('https://blobs.duckdb.org/ams_walk_nodes.geojson');
        CREATE TABLE ams_walk_edges AS SELECT * FROM st_read('https://blobs.duckdb.org/ams_walk_edges.geojson');
    """)

    if not os.path.exists("data"):
        os.mkdir("data")

    nodes_df = conn.execute("SELECT * FROM ams_walk_nodes").fetchdf()
    edges_df = conn.execute("SELECT * FROM ams_walk_edges").fetchdf()
    nodes_df.to_csv("data/nodes.csv", index=False)
    edges_df.to_csv("data/edges.csv", index=False)

    return nodes_df, edges_df


def load_local(conn):
    conn.execute(f"""
        CREATE TABLE nodes AS 
        SELECT * FROM read_csv_auto('data/nodes.csv');
        CREATE TABLE edges AS 
        SELECT * FROM read_csv_auto('data/edges.csv');
    """)
    nodes_raw = conn.execute("SELECT * FROM nodes").fetchall()
    edges_raw = conn.execute("SELECT * FROM edges").fetchall()
    nodes = [
        {
            'name': row[0],
            'geom': decode_if_bytes(row[1]),
        }
        for row in nodes_raw
    ]

    return nodes, edges_raw
