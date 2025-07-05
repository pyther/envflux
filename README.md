# Envflux

**Envflux** is a data logger for Enphase Envoy solar systems. It collects solar production, inverter, and consumption metrics and writes them to InfluxDB for long-term storage and visualization.

Envflux is written in modern Python and supports clean shutdowns, token caching, retry logic, and flexible deployment either as a script or container.


## Project Background

This project was inspired by [amykyta3/envoy-logger](https://github.com/amykyta3/envoy-logger), which provided basic logging functionality for Enphase systems. When additional capabilities were needed—including more detailed inverter metrics and improved reliability—a new implementation was developed.

Envflux uses the [pyenphase](https://github.com/pyenphase/pyenphase) library to handle all communication with the Enphase Envoy API. This project focuses on data processing and persistence to InfluxDB, while `pyenphase` handles the lower-level API integration.

## Features

- Collects CT meter, system, and inverter data from Enphase Envoy
- Formats and writes data to InfluxDB 2.x using line protocol
- Caches authentication tokens on disk
- Retries failed writes with in-memory queueing
- Clean shutdown via signal handling

## Configuration

Create a `config.yaml` file with your connection settings:

```yaml
envoy:
  host: 192.168.1.100
  username: installer
  password: your_password

influxdb:
  url: http://localhost:8086
  token: your_token
  org: your_org
  bucket: envoy
```

## Installation and Usage

### Run from Source

```bash
git clone https://github.com/pyther/envflux.git
cd envflux
python3 -m venv venv
source venv/bin/activate
pip install .
```

Run the app:
```bash
python -m envflux --config path/to/config.yaml
```

Dry-run (for testing):
```bash
python -m envflux --config path/to/config.yaml --dry-run
```

### Run from Container
Build the container
```bash
docker build -t envflux:latest .
```

Prepare config and cache directories
```bash
mkdir -p /srv/envflux/config /srv/envflux/cache
cp config.yaml /srv/envflux/config/config.yaml
```

Run the container
```
docker run -d \
  --name envflux \
  --network host \
  -v /srv/envflux/config/config.yaml:/config/config.yaml:ro \
  -v /srv/envflux/cache:/home/appuser/.cache/envflux:rw \
  envflux:latest
```

## Running with Podman and Systemd
Example systemd container units:

### envflux container
`/etc/containers/systemd/envflux.container`
```
[Unit]
Description=Envflux: Envoy Solar Data Logger Service
Requires=influxdb.service
After=network-online.target influxdb.service

[Container]
ContainerName=envflux
Image=envflux:latest
Network=host
Volume=/srv/envflux/config.yaml:/config/config.yaml:Z,ro
Volume=/srv/envflux/cache:/home/appuser/.cache/envflux:Z,rw


[Install]
WantedBy=multi-user.target
```

### Influx Container
`/etc/containers/systemd/influxdb.container`
```
[Unit]
Description=InfluxDB
Wants=network.target
After=network-online.target

[Container]
ContainerName=influxdb
Image=docker.io/library/influxdb:latest
Network=host
Volume=/srv/influxdb/data:/var/lib/influxdb2:Z
Volume=/srv/influxdb/config:/etc/influxdb2:Z
#Environment=DOCKER_INFLUXDB_INIT_MODE=setup
#Environment=DOCKER_INFLUXDB_INIT_USERNAME=admin
#Environment=DOCKER_INFLUXDB_INIT_PASSWORD=SolarDataRocks1234
#Environment=DOCKER_INFLUXDB_INIT_ORG=home
#Environment=DOCKER_INFLUXDB_INIT_BUCKET=envoy

[Install]
WantedBy=multi-user.target
```

## InfluxDB Measurements

Check out the [InfluxDB Measurements](docs/influxdb-measurements.md) document for detailed measurement information.

## Examples

Check out the [InfluxDB Queries & Grafana Dashboard Examples](docs/influxdb-queries.md) document for detailed example queries and screenshots.
