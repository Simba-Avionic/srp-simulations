import json
from pathlib import Path
from typing import Dict, Any
from parsers.utils import increment_port
from . import settings

BASE_OUTPUT_DIR = (Path(__file__).resolve().parent / "../app/services").resolve()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r") as f:
        return json.load(f)


def generate_server_code(parsed_config: Dict[str, Any], ttl=255) -> tuple[str, str]:
    services = parsed_config["someip"]
    service_name = ""

    service_code = f"""
import ipaddress
import asyncio
from loguru import logger

from someipy import (
    construct_server_service_instance,
    TransportLayerProtocol,
    ServiceBuilder,
    EventGroup
)
from parsers.settings import INTERFACE_IP
"""

    # --- imports ---
    for s_name, service_config in services.items():
        service_name = s_name
        for event_name in service_config.get("events", {}).keys():
            service_code += (
                f"from app.dataclasses.{s_name.lower()}_dataclass import {event_name}Out\n"
            )

    # --- class header ---
    service_code += f"""
class {service_name}:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super({service_name}, cls).__new__(cls)
        return cls._instance

    def __init__(self, service_discovery):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.service_discovery = service_discovery
        self.instance = None
        self.initialized = True
"""

    # --- compute event group once ---
    for s_name, service_config in services.items():
        events = service_config.get("events", {})
        event_group_id = next(iter(events.values()))["id"] if events else None

        # --- send_* methods ---
        for event_name, event_config in events.items():
            event_id = event_config["id"]

            service_code += f"""
    def send_{event_name.lower()}(self, data_value):
        if not self.instance:
            logger.warning("Service not running, cannot send {event_name}")
            return

        msg = {event_name}Out()
        msg.from_json(data_value)
        logger.debug(f"Sending {event_name}: {{data_value}}")

        self.instance.send_event(
            event_group_id={event_group_id},
            event_id={event_id},
            payload=msg.serialize()
        )
"""

    # --- init_service ---
    service_code += """
    async def init_service(self):
        if self.instance:
            return
"""

    for s_name, service_config in services.items():
        events = service_config.get("events", {})
        event_ids = [e["id"] for e in events.values()]
        event_group_id = event_ids[0] if event_ids else None

        if event_ids:
            service_code += f"""
        event_group = EventGroup(
            id={event_group_id},
            event_ids={event_ids}
        )
"""

        service_code += f"""
        service_def = (
            ServiceBuilder()
            .with_service_id({service_config["service_id"]})
            .with_major_version({service_config["major_version"]})"""

        if event_ids:
            service_code += """
            .with_eventgroup(event_group)"""

        service_code += f"""
            .build()
        )

        self.instance = await construct_server_service_instance(
            service=service_def,
            instance_id=1,
            endpoint=(ipaddress.IPv4Address(INTERFACE_IP), {settings.NEXT_PORT}),
            ttl={ttl},
            sd_sender=self.service_discovery,
            cyclic_offer_delay_ms=2000,
            protocol=TransportLayerProtocol.UDP,
        )

        self.service_discovery.attach(self.instance)
        self.instance.start_offer()
        logger.info(f"{service_name} Server Started on port {settings.NEXT_PORT}")
"""
        increment_port()

    # --- shutdown ---
    service_code += """
    async def shutdown(self):
        if self.instance:
            await self.instance.stop_offer()
            self.instance = None
            logger.info("Service Stopped")
"""

    # --- initializer ---
    service_code += f"""
async def initialize_{service_name.lower()}(sd):
    service_manager = {service_name}(sd)
    await service_manager.init_service()
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("Shutting down {service_name}...")
    finally:
        await service_manager.shutdown()
"""

    return service_code, service_name


def process_directory(directory_path: Path):
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating EVENT-ONLY SERVER manager files...")

    for file in directory_path.rglob("*.json"):
        if file.name.endswith("data_type.json"):
            continue

        print(f"Processing {file}...")
        data = load_json(file)
        code, name = generate_server_code(data)

        output_path = BASE_OUTPUT_DIR / f"{name.lower()}.py"
        output_path.write_text(code)
        print(f"Generated: {output_path}")


if __name__ == "__main__":
    process_directory(
        Path("/home/krzysztof/projects/srp-simulations/system_definition/someip/")
    )
