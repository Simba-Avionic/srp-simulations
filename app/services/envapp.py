
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
from app.dataclasses.envapp_dataclass import newTempEvent_1Out
from app.dataclasses.envapp_dataclass import newTempEvent_2Out
from app.dataclasses.envapp_dataclass import newTempEvent_3Out
from app.dataclasses.envapp_dataclass import newPressEventOut

class EnvApp:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EnvApp, cls).__new__(cls)
        return cls._instance

    def __init__(self, service_discovery):
        if hasattr(self, 'initialized') and self.initialized:
            return
            
        self.service_discovery = service_discovery
        self.instance = None
        self.initialized = True

    def send_newtempevent_1(self, data_value):
        if not self.instance:
            logger.warning("Service not running, cannot send newTempEvent_1")
            return

        msg = newTempEvent_1Out()
        msg.from_json(data_value)
        logger.debug(f"Sending newTempEvent_1: {data_value}")
        
        self.instance.send_event(
            event_group_id=32769, 
            event_id=32769, 
            payload=msg.serialize()
        )

    def send_newtempevent_2(self, data_value):
        if not self.instance:
            logger.warning("Service not running, cannot send newTempEvent_2")
            return

        msg = newTempEvent_2Out()
        msg.from_json(data_value)
        logger.debug(f"Sending newTempEvent_2: {data_value}")
        
        self.instance.send_event(
            event_group_id=32770, 
            event_id=32770, 
            payload=msg.serialize()
        )

    def send_newtempevent_3(self, data_value):
        if not self.instance:
            logger.warning("Service not running, cannot send newTempEvent_3")
            return

        msg = newTempEvent_3Out()
        msg.from_json(data_value)
        logger.debug(f"Sending newTempEvent_3: {data_value}")
        
        self.instance.send_event(
            event_group_id=32771, 
            event_id=32771, 
            payload=msg.serialize()
        )

    def send_newpressevent(self, data_value):
        if not self.instance:
            logger.warning("Service not running, cannot send newPressEvent")
            return

        msg = newPressEventOut()
        msg.from_json(data_value)
        logger.debug(f"Sending newPressEvent: {data_value}")
        
        self.instance.send_event(
            event_group_id=32772, 
            event_id=32772, 
            payload=msg.serialize()
        )

    async def init_service(self):
        if self.instance: 
            return
    
        event_group = EventGroup(
            id=32769, 
            event_ids=[32769, 32770, 32771, 32772]
        )
        service_def = (
            ServiceBuilder()
            .with_service_id(514)
            .with_major_version(1)
            .with_eventgroup(event_group)
            .build()
        )

        self.instance = await construct_server_service_instance(
            service=service_def,
            instance_id=1,
            endpoint=(ipaddress.IPv4Address(INTERFACE_IP), 10127),
            ttl=255,
            sd_sender=self.service_discovery,
            cyclic_offer_delay_ms=2000,
            protocol=TransportLayerProtocol.UDP,
        )
        
        self.service_discovery.attach(self.instance)
        self.instance.start_offer()
        logger.info(f"EnvApp Server Started on port 10127")

    async def shutdown(self):
        if self.instance:
            await self.instance.stop_offer()
            self.instance = None
            logger.info("Service Stopped")

async def initialize_envapp(sd):
    service_manager = EnvApp(sd)
    await service_manager.init_service()
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("Shutting down EnvApp...")
    finally:
        await service_manager.shutdown()
