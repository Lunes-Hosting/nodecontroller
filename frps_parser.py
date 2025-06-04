import requests

class FrpsDirectory:
    def __init__(self, dashboard_url, user=None, password=None):
        self.dashboard_url = dashboard_url.rstrip('/')
        self.user = user
        self.password = password
        self.clients = {}

    def fetch_online_clients(self):
        url = f"{self.dashboard_url}/api/proxy/http"
        auth = (self.user, self.password) if self.user and self.password else None
        resp = requests.get(url, auth=auth, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        self._parse_clients(data)

    def _parse_clients(self, data):
        clients = {}
        for proxy in data.get('proxies', []):
            proxy_name = proxy.get('name')
            conf = proxy.get('conf', {})
            domains = conf.get('custom_domains', [])
            clients[proxy_name] = domains
        self.clients = clients

    def get_clients(self):
        return self.clients
