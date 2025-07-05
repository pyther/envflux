import asyncio
import argparse
import logging
import signal
import sys

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from .config import load_config
from .token_manager import TokenManager
from .failed_queue import FailedPointsQueue
from .tracker import InverterUpdateTracker
from .points import generate_points
from .influx import influx_write_points_with_queue
from pyenphase import Envoy

shutdown_event = asyncio.Event()
logger = logging.getLogger(__name__)
MAX_FAILED_POINTS = 10000

def _signal_handler(sig=None, frame=None):
    logger.info("Shutdown signal received, stopping...")
    shutdown_event.set()


def parse_args():
    parser = argparse.ArgumentParser(description="Envoy data collector")
    parser.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration YAML file (default: config.yaml)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without sending data to InfluxDB, print points instead"
    )
    return parser.parse_args()


async def main(config_path="config.yaml", dry_run=False):
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    config = load_config(config_path)
    envoy_host = config["envoy"]["host"]
    envoy_username = config["envoy"]["username"]
    envoy_password = config["envoy"]["password"]
    influx_url = config["influxdb"]["url"]
    influx_token = config["influxdb"]["token"]
    influx_org = config["influxdb"]["org"]
    influx_bucket = config["influxdb"]["bucket"]
    failed_points_queue = FailedPointsQueue(MAX_FAILED_POINTS)
    tracker = InverterUpdateTracker()

    logger.info('Connecting to Envoy')
    envoy: Envoy = Envoy(envoy_host)
    try:
        await envoy.setup()
    except Exception as e:
        logger.error(f"Failed to connect to Envoy during setup: {e}")
        sys.exit(1)

    token_mgr = TokenManager(envoy)

    await token_mgr.authenticate(envoy_username, envoy_password)

    influx_client = None
    write_api = None
    if dry_run:
        logger.info("Running in dry-run mode. Skipping InfluxDB connection.")
    else:
        influx_client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)

    logger.info('Starting main loop')
    while not shutdown_event.is_set():
        await token_mgr.refresh_if_needed()

        try:
            data = await envoy.update()
            points = generate_points(data, tracker)

            for p in points:
                logger.debug(f"Point: {p.to_line_protocol()}")

            if not dry_run:
                await influx_write_points_with_queue(write_api, influx_bucket, points, failed_points_queue)
        except Exception as e:
            logger.error(f"Failed to fetch or process data from Envoy: {e}")

        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=30)
        except asyncio.TimeoutError:
            pass

    logger.info("Cleanup before shutdown...")
    if influx_client:
        write_api.flush()
        influx_client.close()
        logger.info("InfluxDB client closed")

    # Close the aiohttp.ClientSession
    if hasattr(envoy, "_client") and not envoy._client.closed:
        await envoy._client.close()
        logger.info("Envoy HTTP session closed")

    logger.info("Shutdown complete")

    return

def main_entry():
    args = parse_args()
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)
    logging.getLogger("pyenphase").setLevel(logging.INFO)

    asyncio.run(main(config_path=args.config, dry_run=args.dry_run))

if __name__ == "__main__":
    main_entry()
