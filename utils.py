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
        insert_swapped_edges_query = """
            INSERT INTO ams_walk_edges (v, u, key, highway, name, bridge, tunnel, geom, length)
            SELECT u, v, key, highway, name, bridge, tunnel, geom, length
            FROM ams_walk_edges;
        """
        conn.execute(insert_swapped_edges_query)

    nodes = conn.execute("""
    SELECT id, 
           ST_X(geom) AS longitude, 
           ST_Y(geom) AS latitude
           FROM ams_walk_nodes;
    """).fetchall()

    edges = conn.execute("SELECT * FROM ams_walk_edges").fetchall()

    return nodes, edges

def shortest_path(conn, source_node, destination_node):
    # Initialize the priority queue with the source node
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS priority_queue (node_id INTEGER, distance DOUBLE, path VARCHAR);")
    conn.execute("DELETE FROM priority_queue;")  # Clear the priority queue for the new calculation
    conn.execute("INSERT INTO priority_queue VALUES (?, ?, ?)", (source_node, 0, str(source_node)))

    # Initialize the visited nodes table
    conn.execute("CREATE TEMP TABLE IF NOT EXISTS visited_nodes (node_id INTEGER PRIMARY KEY, distance DOUBLE);")
    conn.execute("DELETE FROM visited_nodes;")  # Clear the visited nodes table for the new calculation

    while True:
        # Get the node with the smallest distance
        current_node = conn.execute("SELECT node_id, distance, path FROM priority_queue ORDER BY distance LIMIT 1;").fetchone()
        if not current_node:
            break  # No more nodes to process, end the loop

        node_id, distance, path = current_node
        if node_id == destination_node:
            print(path)
            return [int(x) for x in path.split("->")], distance  # Destination reached

        # Mark the current node as visited
        conn.execute("INSERT OR IGNORE INTO visited_nodes VALUES (?, ?);", (node_id, distance))
        conn.execute("DELETE FROM priority_queue WHERE node_id = ?;", (node_id,))

        # Add neighboring nodes to the priority queue
        neighbors = conn.execute("SELECT v AS neighbor, length FROM ams_walk_edges WHERE u = ? UNION SELECT u AS neighbor, length FROM ams_walk_edges WHERE v = ?;", (node_id, node_id)).fetchall()
        for neighbor, edge_length in neighbors:
            if neighbor in [row[0] for row in conn.execute("SELECT node_id FROM visited_nodes;").fetchall()]:
                continue  # Skip if the neighbor is already visited

            old_distance = conn.execute(f"SELECT distance FROM priority_queue  AS pq WHERE pq.node_id = {neighbor};").fetchone()
            new_distance = distance + edge_length
            if old_distance is None or old_distance[0] > new_distance:
                new_path = path + '->' + str(neighbor)
                conn.execute("INSERT INTO priority_queue VALUES (?, ?, ?);", (neighbor, new_distance, new_path))
        
    return None  # Return None if no path is found

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
