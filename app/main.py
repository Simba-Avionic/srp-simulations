import asyncio
import json
import logging
import csv
from datetime import datetime

from someipy.logging import set_someipy_log_level
from someipy.service_discovery import construct_service_discovery

from parsers.settings import MULTICAST_GROUP, SD_PORT, INTERFACE_IP

from app.services.engineservice import initialize_engineservice, EngineService
from app.services.envapp import initialize_envapp, EnvApp
from app.services.fileloggerapp import initialize_fileloggerapp, FileLoggerApp
from app.services.gpsservice import initialize_gpsservice, GPSService
from app.services.mainservice import initialize_mainservice, MainService
from app.services.primerservice import initialize_primerservice, PrimerService
from app.services.recoveryservice import initialize_recoveryservice, RecoveryService
from app.services.servoservice import initialize_servoservice, ServoService

from loguru import logger
from contextlib import asynccontextmanager

async def initialize_service_discovery():
    sd = await construct_service_discovery(MULTICAST_GROUP, SD_PORT, INTERFACE_IP)
    return sd

async def run_engine_service_manager(sd):
    await initialize_engineservice(sd)

async def run_env_service_manager(sd):
    await initialize_envapp(sd)

async def run_servo_service_manager(sd):
    await initialize_servoservice(sd)

async def run_fileloggerapp_manager(sd):
    await initialize_fileloggerapp(sd)

async def run_primerservice_manager(sd):
    await initialize_primerservice(sd)

async def run_mainservice_manager(sd):
    await initialize_mainservice(sd)

async def run_gpsservice_manager(sd):
    await initialize_gpsservice(sd)

async def run_recovery_manager(sd):
    await initialize_recoveryservice(sd)

@asynccontextmanager
async def lifespan():
    sd_instance = await initialize_service_discovery()
    set_someipy_log_level(logging.INFO)

    tasks = [
        asyncio.create_task(run_engine_service_manager(sd_instance)),
        asyncio.create_task(run_env_service_manager(sd_instance)),
        asyncio.create_task(run_servo_service_manager(sd_instance)),
        asyncio.create_task(run_fileloggerapp_manager(sd_instance)),
        asyncio.create_task(run_primerservice_manager(sd_instance)),
        asyncio.create_task(run_mainservice_manager(sd_instance)),
        asyncio.create_task(run_gpsservice_manager(sd_instance)),
        asyncio.create_task(run_recovery_manager(sd_instance)),
    ]

    try:
        yield sd_instance
    finally:
        logger.info("Shutting down all services...")
        for t in tasks:
            t.cancel()
        for t in tasks:
            try:
                await t
            except asyncio.CancelledError:
                pass
        
        sd_instance.close()
        logger.info("Service discovery shutdown complete.")



async def run_events(sd_instance, json_path="input.json"):
    start_time = datetime.now().timestamp()

    try:
        with open(json_path) as f:
            data = json.load(f)

        # Flatten all events across services and attach service name
        all_events = []
        for service_name, events in data.items():
            for event in events:
                all_events.append({
                    "service": service_name,
                    **event
                })

        # Sort all events globally by seconds_after_start
        all_events_sorted = sorted(all_events, key=lambda x: x["seconds_after_start"])

        # Execute events in chronological order
        for event in all_events_sorted:
            service_name = event["service"]
            event_name = event["event"]
            value = event["value"]
            exec_time = float(event["seconds_after_start"])

            now = datetime.now().timestamp()
            await asyncio.sleep(max(0, exec_time - (now - start_time)))

            # Get the service instance dynamically
            service_class = globals().get(service_name)
            if service_class:
                manager_instance = service_class(sd_instance)
                method_name = f"send_{event_name.strip().lower()}"
                method = getattr(manager_instance, method_name, None)
                if method:
                    method(value)  # value can be number, string, or dict
                else:
                    logger.warning(f"Method {method_name} not found in {service_name}")
            else:
                logger.warning(f"{service_name} class not found")
                
    except FileNotFoundError:
        logger.warning(f"JSON file '{json_path}' not found. No events will be sent.")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file '{json_path}': {e}")
        
async def main():
    async with lifespan() as sd:
        await run_events(sd)
        logger.info("All events dispatched. Simulation running. Press Ctrl+C to stop.")
        await asyncio.Event().wait()

if __name__ == "__main__":
    logger.add("srp-simulations.log", rotation="5 MB")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Simulation stopped by user.")