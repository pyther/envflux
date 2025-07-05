#!/usr/bin/env python3

import logging
from influxdb_client import Point
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class PointBuilder:
    @staticmethod
    def build(measurement, data, fields, tags=None, time_field=None):
        point = Point(measurement)

        # Apply tags from dict
        for tag_name, tag_value in (tags or {}).items():
            if tag_value is not None:
                point.tag(tag_name, tag_value)

        # Apply fields
        for field_name in fields:
            value = getattr(data, field_name)
            point.field(field_name, value)

        # Apply timestamp if specified, otherwise use current UTC time
        ts = None
        if time_field:
            ts = getattr(data, time_field, None)

        if ts is not None:
            point.time(datetime.fromtimestamp(ts, timezone.utc))
        else:
            # Assign current UTC time if no timestamp provided
            point.time(datetime.now(timezone.utc))

        return point

def create_ctmeter_point(measurement, data, phase=None):
    tags = {"eid": data.eid}
    fields = [
        "energy_delivered", "energy_received", "active_power",
        "power_factor", "voltage", "current", "frequency"
    ]
    if phase:
        tags["phase"] = phase
    return PointBuilder.build(measurement, data, fields, tags, "timestamp")


def create_system_point(measurement, data, phase=None):
    tags = {}
    fields = [
        "watt_hours_lifetime", "watt_hours_last_7_days",
        "watt_hours_today", "watts_now"
    ]
    if phase:
        tags["phase"] = phase
    return PointBuilder.build(measurement, data, fields, tags)


def create_inverter_point(measurement, data):
    tags = {"serial_number": data.serial_number}
    fields = [
        "last_report_watts", "max_report_watts", "dc_voltage", "dc_current",
        "ac_voltage", "ac_current", "ac_frequency", "temperature",
        "lifetime_energy", "energy_produced", "energy_today", "last_report_duration"
    ]
    return PointBuilder.build(measurement, data, fields, tags, "last_report_date")


def create_ctmeter_phases_points(measurement, data):
    return [create_ctmeter_point(measurement, phase_data, phase) for phase, phase_data in data.items()]


def create_system_phases_points(measurement, data):
    return [create_system_point(measurement, phase_data, phase) for phase, phase_data in data.items()]

def generate_points(data, inverter_tracker):
    points = []

    # Helper Functions
    def add_point(measurement, datum, creator_func):
        points.append(creator_func(measurement, datum))

    def add_phase_points(measurement, datum, creator_func):
        points.extend(creator_func(measurement, datum))

    # Configurable point mappings
    single_ctmeter_sources = [
        ('ctmeter_consumption', data.ctmeter_consumption),
        ('ctmeter_production', data.ctmeter_production),
    ]

    phased_ctmeter_sources = [
        ('ctmeter_consumption_phases', data.ctmeter_consumption_phases),
        ('ctmeter_production_phases', data.ctmeter_production_phases),
    ]

    single_system_sources = [
        ('system_consumption', data.system_consumption),
        ('system_production', data.system_production),
        ('system_net_consumption', data.system_net_consumption),
    ]

    phased_system_sources = [
        ('system_consumption_phases', data.system_consumption_phases),
        ('system_production_phases', data.system_production_phases),
        ('system_net_consumption_phases', data.system_net_consumption_phases),
    ]

    # Generate Points
    for measurement, datum in single_ctmeter_sources:
        add_point(measurement, datum, create_ctmeter_point)

    for measurement, datum in phased_ctmeter_sources:
        add_phase_points(measurement, datum, create_ctmeter_phases_points)

    for measurement, datum in single_system_sources:
        add_point(measurement, datum, create_system_point)

    for measurement, datum in phased_system_sources:
        add_phase_points(measurement, datum, create_system_phases_points)

    inverter_new_data = []
    for inverter_data in data.inverters.values():
        serial_number = inverter_data.serial_number
        last_report_date = inverter_data.last_report_date

        # Detect if this is truly new (not just first seen)
        previously_seen = inverter_tracker.has_seen(serial_number)

        if inverter_tracker.should_update(serial_number, last_report_date):
            points.append(create_inverter_point('inverters', inverter_data))
            if previously_seen:
                inverter_new_data.append(serial_number)

    if inverter_new_data:
        logger.info(f"Inverters reported new data: {', '.join(inverter_new_data)}")

    return points
