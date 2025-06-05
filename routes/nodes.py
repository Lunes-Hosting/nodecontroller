from flask import Blueprint, request
import datetime
from database_manager import DatabaseManager as db
from apscheduler.schedulers.background import BackgroundScheduler
from flask_restx import Api, Resource, fields
import secrets


# Create the blueprint
nodes_bp = Blueprint('nodes', __name__)

api = Api(nodes_bp, 
    version='1.0',
    title='Nodes API',
    description='API for managing nodes',
    doc='/docs'  # Swagger UI will be available at /nodes/docs
)

# Define the namespace
ns = api.namespace('', description='Node operations')

# Define data models for documentation and validation
node_model = api.model('Node', {
    'id': fields.Integer(description='Node ID', example=1),
    'name': fields.String(description='Node name', example='node-01'),
    'hostname': fields.String(description='Node hostname', example='node.lunes.host'),
    'disk_available': fields.Integer(description='Available disk space in bytes', example=500),
    'status': fields.String(description='Node status', example='active', enum=['active', 'down']),
    'last_seen': fields.String(description='Last seen timestamp', example='2024-01-15 10:30:00')
})

node_input_model = api.model('NodeInput', {
    'name': fields.String(required=True, description='Node name', example='node-01'),
    'hostname': fields.String(required=True, description='Node hostname', example='node.lunes.host'),
    'disk_available': fields.Integer(required=True, description='Available disk space in bytes', example=500)
})

node_response_model = api.model('NodeResponse', {
    'message': fields.String(description='Response message'),
    'id': fields.Integer(description='Node ID'),
    'private_key': fields.String(description='Generated private key')
})


error_model = api.model('Error', {
    'error': fields.String(description='Error message')
})

success_model = api.model('Success', {
    'message': fields.String(description='Success message')
})


def make_private_key(length=32):
    return secrets.token_hex(length)


@ns.route('/list')
class NodeList(Resource):
    @api.doc('list_nodes')
    @api.marshal_list_with(node_model)
    def get(self):
        """Fetch all trusted nodes"""
        try:
            rows = db.execute_query(
                'SELECT id, name, hostname, disk_available, status, last_seen FROM nodes', 
                fetch_all=True
            )
            nodes = [dict(row) for row in rows]
            return nodes
        except Exception as e:
            api.abort(500, f"Database error: {str(e)}")


@ns.route('/add')
class NodeAdd(Resource):
    @api.doc('add_node')
    @api.expect(node_input_model)
    @api.marshal_with(node_response_model, code=201)
    @api.response(400, 'Validation error', error_model)
    @api.response(500, 'Server error', error_model)
    def post(self):
        """Add a new node"""
        data = api.payload
        
        if not data:
            api.abort(400, "No JSON data provided")

        # Validate required fields
        required_fields = ['name', 'hostname', 'disk_available']
        for field in required_fields:
            if field not in data:
                api.abort(400, f"Missing required field: {field}")

        private_key = make_private_key(32)
        
        # Prepare query (let 'id' auto-increment)
        query = """
            INSERT INTO nodes (name, hostname, disk_available, status, last_seen, private_key)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        values = (
            data['name'],
            data['hostname'],
            data['disk_available'],
            "down",  # default status
            None,     # default last_seen
            private_key
        )

        try:
            conn, cursor = db.get_connection()
            cursor.execute(query, values)
            node_id = cursor.lastrowid
            conn.commit()
            return {
                "message": "Node added successfully", 
                "id": node_id, 
                "private_key": private_key
            }, 201

        except Exception as e:
            api.abort(500, f"Database error: {str(e)}")



keep_alive_model = api.model('KeepAlive', {
    'id': fields.Integer(required=True, description='Node ID', example=1),
    'key': fields.String(required=True, description='Private key 32 chracters long', example='1234567890abcdef1234567890abcdef'),
    'disk_used': fields.Integer(required=False, description='Used disk space in bytes', example=500)
})
@ns.route('/keep_alive')
class NodeKeepAlive(Resource):
    @api.doc('keep_alive')
    @api.expect(keep_alive_model)
    @api.marshal_with(success_model)
    @api.response(400, 'Validation error', error_model)
    @api.response(500, 'Server error', error_model)
    def post(self):
        """Update node's last seen timestamp and set status to active"""
        data: dict = api.payload
        
        if not data:
            api.abort(400, "No JSON data provided")
            
        node_id = data.get('id')
        node_key = data.get('key')
        disk_used = data.get('disk_used', None)
        if not node_id:
            api.abort(400, "Missing required field: id")
        if not node_key:
            api.abort(400, "Missing required field: key")
            
        try:
            result = db.execute_query("SELECT id FROM nodes WHERE id = ? AND private_key = ?", (node_id, node_key))
            if result is None:
                api.abort(400, "Invalid node key")
        except Exception as e:
            api.abort(500, f"Database error: {str(e)}")

        try:
            if disk_used is None:
                db.execute_query(
                    "UPDATE nodes SET last_seen = datetime('now'), status = 'active' WHERE id = ?",
                    (node_id,)
                )
            else:
                db.execute_query(
                    "UPDATE nodes SET last_seen = datetime('now'), status = 'active', disk_available = ? WHERE id = ?",
                    (disk_used, node_id)
                )
            return {"message": "Node updated successfully"}
        except Exception as e:
            api.abort(500, f"Database error: {str(e)}")


# Background task functions
def check_node_status():
    """
    Checks all nodes and sets status to 'down' if they haven't been seen in 10+ minutes.
    This function is designed to be scheduled to run periodically.
    """
    # Calculate the timestamp for 10 minutes ago
    ten_minutes_ago = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)  # Fixed: was 1 minute
    cutoff_time = ten_minutes_ago.strftime('%Y-%m-%d %H:%M:%S')
    
    # Find and update nodes that haven't been seen recently
    query = """
    UPDATE nodes 
    SET status = 'down' 
    WHERE (last_seen < ? OR last_seen IS NULL) 
    AND status != 'down'
    """
    
    try:
        affected_rows = db.execute_query(query, (cutoff_time,))
        print(f"Node status check complete: {affected_rows} nodes marked as down")
    except Exception as e:
        print(f"Error updating node status: {e}")


# Set up the scheduler
def setup_node_status_scheduler():
    """
    Sets up a background scheduler to periodically check node status.
    Call this function when your application starts.
    """
    scheduler = BackgroundScheduler()
    # Run every minute
    scheduler.add_job(check_node_status, 'interval', minutes=1)
    scheduler.start()
    print("Node status monitoring scheduler started")
    
    # If you're in a Flask application, you might want to shut down the scheduler when the app exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())


# Initialize the scheduler
setup_node_status_scheduler()