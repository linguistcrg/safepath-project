import os


def table_exists(conn, table_name):
    result = conn.execute(f"""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_name = '{table_name}'
    """).fetchone()
    return result[0] > 0


def load_from_url(conn):
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    conn.install_extension("httpfs")
    conn.load_extension("httpfs")

    if not table_exists(conn, 'ams_walk_nodes'):

        conn.execute("""
            CREATE TABLE ams_walk_nodes AS SELECT * FROM st_read('https://blobs.duckdb.org/ams_walk_nodes.geojson');
            CREATE TABLE ams_walk_edges AS SELECT * FROM st_read('https://blobs.duckdb.org/ams_walk_edges.geojson');
        """)

    nodes = conn.execute("""
    SELECT id, 
           ST_X(geom) AS longitude, 
           ST_Y(geom) AS latitude
           FROM ams_walk_nodes;
    """).fetchall()
    edges = conn.execute("SELECT * FROM ams_walk_edges").fetchall()

    return nodes, edges


def shortest_path(conn, source_node, destination_node):
    shortest_path_query = f"""
    WITH RECURSIVE ShortestPath AS (
        -- Base case: Initialize with the source node
        SELECT
            u AS node_id,
            CAST(u AS VARCHAR) AS path,
            0 AS distance
        FROM
            ams_walk_edges
        WHERE
            u = {source_node} -- Replace with the source node ID
    
        UNION ALL
    
        -- Recursive step: Expand the path
        SELECT
            ams_walk_edges.v AS node_id,
            ShortestPath.path || '->' || CAST(ams_walk_edges.v AS VARCHAR) AS path,
            ShortestPath.distance + 1 AS distance
        FROM
            ShortestPath
        JOIN
            ams_walk_edges ON ShortestPath.node_id = ams_walk_edges.u
        WHERE
            ams_walk_edges.v <> {source_node}
    )
    SELECT
        path,
        distance
    FROM
        ShortestPath
    WHERE
        node_id = {destination_node}
    ORDER BY
        distance;
    """

    path = conn.execute(shortest_path_query).fetchone()
    if path is not None:
        return [int(x) for x in path[0].split("->")], path[1]
    return None
