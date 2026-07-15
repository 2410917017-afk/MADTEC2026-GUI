import requests

from hmi.config import HTTP_TIMEOUT_SECONDS


class ApiClient:
    def __init__(self, base_url: str, timeout: int = HTTP_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def list_cases(self):
        return self._request("get", "/casos")

    def get_case(self, case_id):
        return self._request("get", f"/casos/{case_id}")

    def create_case(self, payload):
        return self._request("post", "/casos", json=payload)

    def update_case(self, case_id, payload):
        return self._request("put", f"/casos/{case_id}", json=payload)

    def delete_case(self, case_id):
        return self._request("delete", f"/casos/{case_id}")

    def create_test(self, payload):
        return self._request("post", "/pruebas", json=payload)

    def create_sample(self, payload):
        return self._request("post", "/datos", json=payload)

    def _request(self, method, path, **kwargs):
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()
        if response.content:
            return response.json()
        return None
