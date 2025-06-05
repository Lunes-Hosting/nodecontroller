from flask import Flask, render_template_string, request
from frps_parser import FrpsDirectory
import threading
import time
from database_manager import DatabaseManager
from routes.nodes import nodes_bp

# Configurations
FRPS_DASHBOARD_URL = 'http://204.10.194.164:7500'  # Change as needed
FRPS_DASHBOARD_USER = "admin"  # Set if dashboard authentication is enabled
FRPS_DASHBOARD_PWD = "admin123"  # Set if dashboard authentication is enabled
REFRESH_INTERVAL = 5  # seconds

directory = FrpsDirectory(FRPS_DASHBOARD_URL, FRPS_DASHBOARD_USER, FRPS_DASHBOARD_PWD)

db = DatabaseManager()

db.execute_query('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY,
                title TEXT,
                year INTEGER
                imdb_id TEXT
            )
            ''')

#example query
"""INSERT INTO nodes (name, hostname, disk_available, status, last_seen) 
VALUES ('Node-Server-1', 'server1.example.com', 100000, 'active', datetime('now'));
"""
db.execute_query('''
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                name TEXT,
                hostname TEXT,
                disk_available INTEGER,
                status TEXT,
                last_seen datetime,
                private_key TEXT
            )
            ''')

db.execute_query('''
            CREATE TABLE IF NOT EXISTS movie_nodes (
                movie_id INT REFERENCES movies(id),
                node_id INT REFERENCES nodes(id),
                PRIMARY KEY (movie_id, node_id)
            )
            ''')


def update_clients_loop():
    while True:
        try:
            directory.fetch_online_clients()
        except Exception as e:
            print(f"Error updating clients: {e}")
        time.sleep(REFRESH_INTERVAL)

threading.Thread(target=update_clients_loop, daemon=True).start()

app = Flask(__name__)

app.register_blueprint(nodes_bp, url_prefix='/nodes')

TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>FRPS Active Directory</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        table { border-collapse: collapse; width: 60%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background: #f2f2f2; }
    </style>
</head>
<body>
    <h2>FRPS Active Clients and Domains</h2>
    <table>
        <tr><th>Client</th><th>Domains</th></tr>
        {% for client, domains in clients.items() %}
        <tr>
            <td>{{ client }}</td>
            <td>{{ ', '.join(domains) if domains else '-' }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(TEMPLATE, clients=directory.get_clients())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
