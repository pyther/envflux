#!/usr/bin/env python3

class FailedPointsQueue:
    def __init__(self, max_size=10000):
        self._queue = []
        self._max_size = max_size

    def add_points(self, points):
        self._queue.extend(points)
        # Keep only newest max_size points to prevent memory bloat
        if len(self._queue) > self._max_size:
            self._queue = self._queue[-self._max_size:]

    def get_all(self):
        return self._queue.copy()

    def clear(self):
        self._queue.clear()

    def is_empty(self):
        return len(self._queue) == 0
