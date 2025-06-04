from flask import Blueprint, request, jsonify
from database_manager import DatabaseManager as db

# Create the blueprint
nodes_bp = Blueprint('nodes', __name__)

@nodes_bp.route('/list', methods=['GET'])
def list_trusted_nodes():
    # Fetch column names first
    columns = [column_info[1] for column_info in db.execute_query("PRAGMA table_info(nodes)", fetch_all=True)]
    
    # Fetch the actual data
    nodes_data = db.execute_query("SELECT * FROM nodes", fetch_all=True)
    
    # Convert tuples to dictionaries with column names as keys
    nodes = []
    for node in nodes_data:
        node_dict = {columns[i]: value for i, value in enumerate(node)}
        nodes.append(node_dict)
    
    return jsonify({"nodes": nodes})

@nodes_bp.route('/add', methods=['POST'])
def add_node():
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'name', 'hostname',]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Insert the node
    query = "INSERT INTO nodes (name, hostname, status, last_seen) VALUES (?, ?, ?, ?)"
    values = (data['name'], data['hostname'], "down", None)
    
    try:
        db.execute_query(query, values)
        return jsonify({"message": "Node added successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@nodes_bp.route('/delete/<int:node_id>', methods=['DELETE'])
def delete_node(node_id):
    query = "DELETE FROM nodes WHERE id = ?"
    
    try:
        db.execute_query(query, (node_id,))
        return jsonify({"message": "Node deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500