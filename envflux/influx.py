#!/usr/bin/env python3

import logging
import random
import asyncio
from influxdb_client.rest import ApiException
from urllib3.exceptions import HTTPError
import socket

logger = logging.getLogger(__name__)

async def influx_write_points_with_queue(write_api, bucket, new_points, failed_queue, retries=3):
    global failed_points

    # Combine new points with backlog
    combined_points = failed_queue.get_all() + new_points

    # Summary print (optional, you can add the summarize_points function from earlier)
    logger.debug(f"Attempting to write {len(combined_points)} points")

    for attempt in range(1, retries + 1):
        try:
            write_api.write(bucket=bucket, record=combined_points)
            write_api.flush()
            logger.debug("Influx write successful.")
            failed_queue.clear()
            return
        except (ApiException, HTTPError, socket.error, ConnectionError) as e:
            logger.info(f"Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                sleep_time = 2 ** attempt + random.uniform(0, 1)
                logger.info(f"Retrying in {sleep_time:.1f} seconds...")
                await asyncio.sleep(sleep_time)
            else:
                logger.error("All retries failed. Queuing points for later.")
                failed_queue.add_points(combined_points)
