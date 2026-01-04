
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
from app.dataclasses.servoservice_dataclass import ServoStatusEventOut
from app.dataclasses.servoservice_dataclass import ServoVentStatusEventOut
from app.dataclasses.servoservice_dataclass import ServoDumpStatusEventOut

class ServoService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ServoService, cls).__new__(cls)
        return cls._instance

    def __init__(self, service_discovery):
        if hasattr(self, "initialized") and self.initialized:
            return

        self.service_discovery = service_discovery
        self.instance = None
        self.initialized = True

    def send_servostatusevent(self, data_value):
        if not self.instance:
            logger.warning("Service not running, cannot send ServoStatusEvent")
            return

        msg = ServoStatusEventOut()
        msg.from_json(data_value)
        logger.debug(f"Sending ServoStatusEvent: {data_value}")

        self.instance.send_event(
            event_group_id=32769,
            event_id=32769,
            payload=msg.serialize()
        )

    def send_servoventstatusevent(self, data_value):
        if not self.instance:
            logger.warning("Service not running, cannot send ServoVentStatusEvent")
            return

        msg = ServoVentStatusEventOut()
        msg.from_json(data_value)
        logger.debug(f"Sending ServoVentStatusEvent: {data_value}")

        self.instance.send_event(
            event_group_id=32769,
            event_id=32770,
            payload=msg.serialize()
        )

    def send_servodumpstatusevent(self, data_value):
        if not self.instance:
            logger.warning("Service not running, cannot send ServoDumpStatusEvent")
            return

        msg = ServoDumpStatusEventOut()
        msg.from_json(data_value)
        logger.debug(f"Sending ServoDumpStatusEvent: {data_value}")

        self.instance.send_event(
            event_group_id=32769,
            event_id=32771,
            payload=msg.serialize()
        )

    async def init_service(self):
        if self.instance:
            return

        event_group = EventGroup(
            id=32769,
            event_ids=[32769, 32770, 32771]
        )

        service_def = (
            ServiceBuilder()
            .with_service_id(515)
            .with_major_version(1)
            .with_eventgroup(event_group)
            .build()
        )

        self.instance = await construct_server_service_instance(
            service=service_def,
            instance_id=1,
            endpoint=(ipaddress.IPv4Address(INTERFACE_IP), 10139),
            ttl=255,
            sd_sender=self.service_discovery,
            cyclic_offer_delay_ms=2000,
            protocol=TransportLayerProtocol.UDP,
        )

        self.service_discovery.attach(self.instance)
        self.instance.start_offer()
        logger.info(f"ServoService Server Started on port 10139")

    async def shutdown(self):
        if self.instance:
            await self.instance.stop_offer()
            self.instance = None
            logger.info("Service Stopped")

async def initialize_servoservice(sd):
    service_manager = ServoService(sd)
    await service_manager.init_service()
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("Shutting down ServoService...")
    finally:
        await service_manager.shutdown()
