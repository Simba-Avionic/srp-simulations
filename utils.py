import yaml

def increment_port(yaml_path="config.yml"):
    with open(yaml_path, "r") as file:
        config = yaml.safe_load(file) or {}

    if "next_port" not in config:
        raise KeyError("'next_port' key not found in config")

    config["next_port"] += 1

    with open(yaml_path, "w") as file:
        yaml.safe_dump(config, file)