from flask import Blueprint, request, jsonify
from database_manager import DatabaseManager as db

# Create the blueprint
nodes_bp = Blueprint('nodes', __name__)

def make_private_key(length=32):
    import secrets
    return secrets.token_hex(length)

@nodes_bp.route('/list', methods=['GET'])
def list_trusted_nodes():
    rows = db.execute_query('SELECT * FROM nodes', fetch_all=True)
    nodes = [dict(row) for row in rows]  # Now each row is a sqlite3.Row
    return jsonify(nodes)

@nodes_bp.route('/add', methods=['POST'])
def add_node():
    data = request.json

    # Validate required fields
    required_fields = ['name', 'hostname', 'disk_available']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Prepare query (let 'id' auto-increment)
    query = """
        INSERT INTO nodes (name, hostname, disk_available, status, last_seen)
        VALUES (?, ?, ?, ?, ?)
    """
    values = (
        data['name'],
        data['hostname'],
        data['disk_available'],
        "down",  # default status
        None     # default last_seen
    )

    try:
        conn, cursor = db.get_connection()
        cursor.execute(query, values)
        node_id = cursor.lastrowid
        conn.commit()
        return jsonify({"message": "Node added successfully", "id": node_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@nodes_bp.route('/keep_alive', methods=['POST'])
def keep_alive():
    data = request.json
    id = data.get('id')
    db.execute_query(
        "UPDATE nodes SET last_seen = datetime('now'), status = 'active' WHERE id = ?",
        (id,)
    )

    return jsonify({"message": "Node updated successfully"}), 200



