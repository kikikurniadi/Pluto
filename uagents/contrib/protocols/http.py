# HTTP protocol shim used by orchestrator_agent
class Httpy:
    def __init__(self, ctx):
        self.ctx = ctx

class HttpyRequest:
    def __init__(self, json):
        self.json = json

class HttpyResponse:
    def __init__(self, status_code=200, json=None):
        self.status_code = status_code
        self.json = json or {}
