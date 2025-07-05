#!/usr/bin/env python3

from pyenphase import Envoy

async def setup_envoy(host):
    envoy = Envoy(host)
    await envoy.setup()
    return envoy
