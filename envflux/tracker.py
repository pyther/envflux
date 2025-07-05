#!/usr/bin/env python3

class InverterUpdateTracker:
    def __init__(self):
        # Maps serial_number -> last known timestamp (epoch seconds)
        self.last_timestamps = {}

    def should_update(self, serial_number, new_timestamp):
        last_ts = self.last_timestamps.get(serial_number)
        if last_ts is None or new_timestamp > last_ts:
            self.last_timestamps[serial_number] = new_timestamp
            return True
        return False

    def has_seen(self, serial):
        return serial in self.last_timestamps
