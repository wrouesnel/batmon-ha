import asyncio

from bleak import BleakScanner
from bmslib.util import get_logger

logger = get_logger()


async def bt_discovery():
    logger.info("BT Discovery:")
    devices = await BleakScanner.discover()
    if not devices:
        logger.info(" - no devices found - ")
    for d in devices:
        logger.info("BT Device   %s   address=%s", d.name, d.address)
    return devices


asyncio.run(bt_discovery())
