import os
def table_exists(conn, table_name):
    """
    Check if a table exists in the database.
    
    :param conn: The database connection object
    :param table_name: The name of the table to check
    :return: True if the table exists, False otherwise
    """
    result = conn.execute(f"""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_name = '{table_name}'
    """).fetchone()
    
    return result[0] > 0

def create_feedback_table(conn):
    """
    Create the feedback table if it does not exist.
    
    :param conn: The database connection object
    """
    if not table_exists(conn, 'feedback'):
        conn.execute("""
        CREATE SEQUENCE feedback_id_seq START 1;
        CREATE TABLE feedback (
            id INTEGER DEFAULT NEXTVAL('feedback_id_seq') PRIMARY KEY,
            nodeOne DOUBLE,
            nodeTwo DOUBLE,
            safety_rating INTEGER,
            lighting_rating INTEGER,
            speed_rating INTEGER,
            overall_rating INTEGER,
            review TEXT
        );
        """)

def load_from_url(conn):
    """
    Load data from URLs into the database and return nodes and edges.
    
    :param conn: The database connection object
    :return: A tuple containing nodes and edges
    """
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
    """
    Calculate the shortest path between two nodes.
    
    :param conn: The database connection object
    :param source_node: The ID of the source node
    :param destination_node: The ID of the destination node
    :return: A tuple containing the path as a list of node IDs and the total distance
    """
    # Define the SQL query for calculating the shortest path
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
            u = {source_node}

        UNION ALL

        -- Recursive step: Expand the path
        SELECT
            ams_walk_edges.v AS node_id,
            ShortestPath.path || '->' || CAST(ams_walk_edges.v AS VARCHAR) AS path,
            ShortestPath.distance + ams_walk_edges.length AS distance
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
    
    # Execute the query and fetch the result
    path = conn.execute(shortest_path_query).fetchone()
    
    # If a path is found, return the path as a list of node IDs and the total distance
    if path is not None:
        return [int(x) for x in path[0].split("->")], path[1]
    
    # Return None if no path is found
    return None

def find_closest_point(conn, longitude, latitude):
    """
    Find the closest point to the given coordinates.
    
    :param conn: The database connection object
    :param longitude: The longitude of the point
    :param latitude: The latitude of the point
    :return: The closest point with its id, longitude, and latitude
    """
    # Define the SQL query to find the closest point
    query = f"""
        SELECT id, 
        ST_X(geom) AS longitude, 
        ST_Y(geom) AS latitude
        FROM ams_walk_nodes
        ORDER BY ST_Distance(
            geom,
            ST_Point({longitude}, {latitude})
        );
    """
    
    # Execute the query and fetch the closest point
    point = conn.execute(query).fetchone()
    
    # If a point is found, return the point
    if point is not None:
        return point
    
    # Return None if no point is found
    return None
