import yaml

N = 6

services = {}
for i in range(1, N + 1):
    port = 8000 + i
    services[f"server{i}"] = {
        "container_name": f"server{i}",
        "build": ".",
        "network_mode": "host",
        "env_file": [".env"],
        "ports": [f"{port}:{port}"],
        "environment": [f"PORT={port}"],
    }

compose = {"services": services}

with open("../../docker-compose_docker-servers.yml", "w") as f:
    yaml.dump(compose, f, sort_keys=False)
