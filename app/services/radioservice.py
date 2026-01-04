
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

class RadioService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RadioService, cls).__new__(cls)
        return cls._instance

    def __init__(self, service_discovery):
        if hasattr(self, 'initialized') and self.initialized:
            return
            
        self.service_discovery = service_discovery
        self.instance = None
        self.initialized = True

    async def init_service(self):
        if self.instance: 
            return
    
        service_def = (
            ServiceBuilder()
            .with_service_id(530)
            .with_major_version(1)
            .build()
        )

        self.instance = await construct_server_service_instance(
            service=service_def,
            instance_id=1,
            endpoint=(ipaddress.IPv4Address(INTERFACE_IP), 10132),
            ttl=255,
            sd_sender=self.service_discovery,
            cyclic_offer_delay_ms=2000,
            protocol=TransportLayerProtocol.UDP,
        )
        
        self.service_discovery.attach(self.instance)
        self.instance.start_offer()
        logger.info(f"RadioService Server Started on port 10132")

    async def shutdown(self):
        if self.instance:
            await self.instance.stop_offer()
            self.instance = None
            logger.info("Service Stopped")

async def initialize_radioservice(sd):
    service_manager = RadioService(sd)
    await service_manager.init_service()
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        logger.info("Shutting down RadioService...")
    finally:
        await service_manager.shutdown()
