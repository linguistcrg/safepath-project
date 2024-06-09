import duckdb
import pandas as pd


def table_exists(conn, table_name):
    """
    Check if a table exists in the database.
    
    :param conn: The database connection object
    :param table_name: The name of the table to check
    :return: True if the table exists, False otherwise
    """
    # Execute an SQL query to count the number of tables with the given name
    result = conn.execute(f"""
    SELECT COUNT(*) 
    FROM information_schema.tables 
    WHERE table_name = '{table_name}'
    """).fetchone()
    
    # Return True if the count is greater than 0
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


def calculate_lightning(conn):
    alter_query = f"""
    WITH NodesAndEdges AS (
        SELECT
            e.u,
            e.v,
            nu.geom AS nu,
            nv.geom AS nv
        FROM
            ams_walk_edges e
        JOIN
            ams_walk_nodes nu ON e.u = nu.id
        JOIN
            ams_walk_nodes nv ON e.v = nv.id
    ),
    LightningCounts AS (
        SELECT
            e.u,
            e.v,
            COUNT(l.id) AS lightning_count
        FROM
            NodesAndEdges e
        JOIN
            ams_lights l
        ON
            (ST_Distance(e.nu, l.geom) <= 0.0009 AND ST_Distance(e.nv, l.geom) <= 0.0009)
        GROUP BY
            e.u, e.v
    )
    UPDATE ams_walk_edges
    SET lightning_count = (
        SELECT lc.lightning_count
        FROM LightningCounts lc
        WHERE lc.u = ams_walk_edges.u AND lc.v = ams_walk_edges.v
    )
    WHERE EXISTS (
        SELECT 1
        FROM LightningCounts lc
        WHERE lc.u = ams_walk_edges.u AND lc.v = ams_walk_edges.v
    );
    """
    conn.execute("ALTER TABLE ams_walk_edges ADD COLUMN lightning_count INTEGER DEFAULT 0;")
    conn.execute(alter_query)


def add_safety_stats(conn):
    alter_query = """
    CREATE TEMPORARY TABLE edge_danger_scores AS
    SELECT
        e.id AS edge_id,
        SUM(c_u.index + c_v.index) AS danger_score
    FROM
        ams_walk_edges e
    JOIN
        ams_walk_nodes n_u ON e.u = n_u.id
    JOIN
        districts d_u ON ST_Within(n_u.geom, d_u.polygon)
    JOIN
        criminals c_u ON d_u.name = c_u.name
    JOIN
        ams_walk_nodes n_v ON e.v = n_v.id
    JOIN
        districts d_v ON ST_Within(n_v.geom, d_v.polygon)
    JOIN
        criminals c_v ON d_v.name = c_v.name
    GROUP BY
        e.id;
    """
    conn.execute("ALTER TABLE ams_walk_edges ADD COLUMN danger_score INTEGER;")
    conn.execute(alter_query)

    # Update the ams_walk_edges table with the calculated danger scores
    conn.execute("""
    UPDATE ams_walk_edges
    SET danger_score = (
        SELECT danger_score
        FROM edge_danger_scores
        WHERE edge_danger_scores.edge_id = ams_walk_edges.id
    );
    """)


def load_from_url(conn):
    """
    Load data from URLs into the database and return nodes and edges.
    
    :param conn: The database connection object
    :return: A tuple containing nodes and edges
    """
    # Install and load the spatial extension
    conn.install_extension("spatial")
    conn.load_extension("spatial")

    # Install and load the httpfs extension
    conn.install_extension("httpfs")
    conn.load_extension("httpfs")

    # Check if the table 'ams_walk_nodes' does not exist
    if not table_exists(conn, 'ams_walk_nodes'):
        # Create tables by reading data from the given URLs
        conn.execute("""
            CREATE TABLE ams_walk_nodes AS SELECT * FROM st_read('https://blobs.duckdb.org/ams_walk_nodes.geojson');
            CREATE TABLE ams_walk_edges AS SELECT * FROM st_read('https://blobs.duckdb.org/ams_walk_edges.geojson');
        """)

        districts_df = pd.read_csv("data/INDELING_WIJK.csv", delimiter=";")
        criminals_df = pd.read_csv("data/criminaliteit-wijken-2023-3.csv", delimiter=",")

        conn.sql("CREATE TABLE districts AS SELECT id, name, ST_GeomFromText(polygon) AS polygon FROM districts_df")
        conn.sql("CREATE TABLE criminals AS SELECT * FROM criminals_df")

        add_safety_stats(conn)

        insert_swapped_edges_query = """
            INSERT INTO ams_walk_edges (v, u, key, highway, name, bridge, tunnel, geom, length, danger_score)
            SELECT u, v, key, highway, name, bridge, tunnel, geom, length, danger_score
            FROM ams_walk_edges;
        """
        conn.execute(insert_swapped_edges_query)

    edges = conn.execute("SELECT danger_score FROM ams_walk_edges WHERE u = 11956 OR v = 11956;").fetchall()

    nodes = conn.execute("""
    SELECT id, 
           ST_X(geom) AS longitude, 
           ST_Y(geom) AS latitude
           FROM ams_walk_nodes;
    """).fetchall()

    # Retrieve all edge data
    edges = conn.execute("SELECT * FROM ams_walk_edges").fetchall()

    # Return the nodes and edges
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
        neighbors = conn.execute("SELECT v AS neighbor, length, danger_score FROM ams_walk_edges"
                                 " WHERE u = ? UNION SELECT u AS neighbor, length, danger_score "
                                 "FROM ams_walk_edges WHERE v = ?;",
                                 (node_id, node_id)).fetchall()

        for neighbor, edge_length, danger_score in neighbors:
            if danger_score is None:
                danger_score = 400
            if neighbor in [row[0] for row in conn.execute("SELECT node_id FROM visited_nodes;").fetchall()]:
                continue  # Skip if the neighbor is already visited

            old_distance = conn.execute(f"SELECT distance FROM priority_queue  AS pq WHERE pq.node_id = {neighbor};").fetchone()
            new_distance = distance + edge_length + danger_score
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
