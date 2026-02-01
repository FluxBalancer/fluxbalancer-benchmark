import yaml

N = 12

services = {}
for i in range(1, N + 1):
    port = 8000 + i
    services[f"server{i}"] = {
        "container_name": f"server{i}",
        "build": ".",
        "ports": [f"{port}:{port}"],
        "environment": [f"PORT={port}"]
    }

compose = {
    "version": "3.9",
    "services": services
}

with open("docker-compose_docker-servers.yml", "w") as f:
    yaml.dump(compose, f, sort_keys=False)
