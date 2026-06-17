import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def request_json(method, path, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    print("GET /")
    print(request_json("GET", "/"))

    print("\nPOST /operations")
    op = request_json(
        "POST",
        "/operations",
        {
            "name": "Compra",
            "symbol": "PETR4",
            "quantity": 10,
            "price": 35.5,
        },
    )
    print(op)

    print("\nGET /operations")
    print(request_json("GET", "/operations"))

    print("\nPOST /simulation")
    sim = request_json(
        "POST",
        "/simulation",
        {
            "initial_value": 1000,
            "monthly_contribution": 200,
            "years": 5,
            "volatility": 0.15,
        },
    )
    print(sim)
