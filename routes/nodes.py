from flask import Blueprint, request, jsonify
from database_manager import DatabaseManager as db

# Create the blueprint
nodes_bp = Blueprint('nodes', __name__)

@nodes_bp.route('/list', methods=['GET'])
def list_trusted_nodes():
    rows = db.execute_query('SELECT * FROM nodes', fetch_all=True)
    nodes = [dict(row) for row in rows]  # Now each row is a sqlite3.Row
    return jsonify(nodes)

@nodes_bp.route('/add', methods=['POST'])
def add_node():
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'name', 'hostname', 'disk_available']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Insert the node
    query = "INSERT INTO nodes (name, hostname, 'disk_available', 'status, last_seen) VALUES (?, ?, ?, ?, ?)"
    values = (data['name'], data['hostname'], data['disk_available'], "down", None)
    
    try:
        db.execute_query(query, values)
        return jsonify({"message": "Node added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

