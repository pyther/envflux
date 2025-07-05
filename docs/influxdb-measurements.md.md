## InfluxDB Measurements

Envflux writes structured data into InfluxDB using several `_measurement` names. This document outlines each measurement along with its associated fields and tags.

---

### `system_production`, `system_consumption`, `system_net_consumption`
**Fields:**
- `watts_now` – Current power in watts
- `watt_hours_today` – Energy produced/consumed today in watt-hours
- `watt_hours_last_7_days` – Energy over the last 7 days
- `watt_hours_lifetime` – Cumulative energy since installation

**Tags:**
- `phase` (optional) – Present when writing per-phase data (`L1`, `L2`, etc.)

---

### `inverters`
**Fields:**
- `last_report_watts` – Power reported in the last update
- `max_report_watts` – Maximum power ever reported
- `dc_voltage` – Input voltage from DC side
- `dc_current` – Input current from DC side
- `ac_voltage` – Output voltage on AC side
- `ac_current` – Output current on AC side
- `ac_frequency` – AC output frequency
- `temperature` – Inverter internal temperature in Celsius
- `lifetime_energy` – Total energy produced over lifetime
- `energy_produced` – Incremental energy since last report
- `energy_today` – Energy generated today
- `last_report_duration` – Time in seconds since last report

**Tags:**
- `serial_number` – Inverter serial number

---

### `ctmeter_production`, `ctmeter_consumption`
**Fields:**
- `energy_delivered` – Energy delivered to the load/grid
- `energy_received` – Energy drawn from the grid
- `active_power` – Current active power (W)
- `power_factor` – Real to apparent power ratio
- `voltage` – Voltage measured
- `current` – Current measured
- `frequency` – Line frequency

**Tags:**
- `eid` – Equipment/device ID
- `phase` (optional) – For per-phase measurements

---

### Phase-Level Measurements
Each of the following measurements has a corresponding per-phase variant:
- `system_production_phases`
- `system_consumption_phases`
- `system_net_consumption_phases`
- `ctmeter_production_phases`
- `ctmeter_consumption_phases`

These include the same fields as their non-phased counterparts, with the addition of a `phase` tag (`L1`, `L2`, etc.).
