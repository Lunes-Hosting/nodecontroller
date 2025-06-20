import requests

def add_node(name, hostname, disk_available):
    url = "http://127.0.0.1:5000/nodes/add"  # Adjust port and path if different
    data = {
        "name": name,
        "hostname": hostname,
        "disk_available": disk_available  # in MB or GB depending on your design
    }
    response = requests.post(url, json=data, timeout=60)
    return response.json()

def keep_alive(id):
    url = "http://127.0.0.1:5000/nodes/keep_alive"  # Adjust port and path if different
    data = {
        "id": id
    }
    response = requests.post(url, json=data, timeout=60)
    return response.json()

# print(add_node("Node-Server-1", "server1.example.com", 100000))
print(keep_alive(1))
