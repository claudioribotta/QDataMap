# coding=utf-8
"""Tests for ResourceMonitor (Section 6.2 of the v1.1 plan).

Runnable without QGIS (qgis modules are stubbed) but require psutil, which is
a mandatory plugin dependency.
"""

import time
import unittest

from .qgis_stubs import load_plugin_module

qdatamap = load_plugin_module()

try:
    import psutil  # noqa: F401
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# All Section 5 fields the monitor must report when sampling succeeds.
EXPECTED_FIELDS = (
    'sampling_interval', 'samples_count', 'cpu_logical_cores',
    'cpu_percent_peak_raw', 'cpu_percent_mean_raw',
    'cpu_percent_peak_normalized', 'cpu_percent_mean_normalized',
    'rss_start', 'rss_peak', 'rss_delta',
)


def synthetic_load(duration, allocate_bytes=0):
    """Busy-loop for `duration` seconds holding `allocate_bytes` of memory."""
    ballast = bytearray(allocate_bytes) if allocate_bytes else None
    deadline = time.monotonic() + duration
    x = 0.0
    while time.monotonic() < deadline:
        x += sum(i * i for i in range(1000))
    return ballast, x


@unittest.skipUnless(PSUTIL_AVAILABLE, 'psutil is required for these tests')
class TestResourceMonitor(unittest.TestCase):

    def test_stop_returns_all_section5_fields(self):
        monitor = qdatamap.ResourceMonitor(interval=0.05)
        monitor.start()
        synthetic_load(0.5)
        metrics = monitor.stop()
        for field in EXPECTED_FIELDS:
            self.assertIn(field, metrics, f'missing field: {field}')

    def test_sample_count_consistent_with_duration(self):
        # Verifies sampling really happens on a separate thread and is not
        # blocked by a busy main thread.
        interval = 0.05
        duration = 1.0
        monitor = qdatamap.ResourceMonitor(interval=interval)
        monitor.start()
        synthetic_load(duration)
        metrics = monitor.stop()
        expected = duration / interval
        self.assertGreaterEqual(metrics['samples_count'], expected * 0.4)
        self.assertLessEqual(metrics['samples_count'], expected * 2.5)

    def test_rss_peak_sensitive_to_allocation(self):
        allocation = 150 * 1024 * 1024  # 150 MB
        monitor = qdatamap.ResourceMonitor(interval=0.05)
        monitor.start()
        ballast, _ = synthetic_load(0.6, allocate_bytes=allocation)
        metrics = monitor.stop()
        del ballast
        # Sensitivity check, not an absolute-value check: the peak must have
        # grown by a substantial fraction of the deliberate allocation.
        self.assertGreaterEqual(metrics['rss_peak'] - metrics['rss_start'],
                                allocation // 2)

    def test_cpu_reported_raw_and_normalized(self):
        monitor = qdatamap.ResourceMonitor(interval=0.05)
        monitor.start()
        synthetic_load(0.5)
        metrics = monitor.stop()
        cores = metrics['cpu_logical_cores']
        self.assertGreaterEqual(cores, 1)
        self.assertAlmostEqual(metrics['cpu_percent_peak_normalized'],
                               metrics['cpu_percent_peak_raw'] / cores, places=6)
        self.assertAlmostEqual(metrics['cpu_percent_mean_normalized'],
                               metrics['cpu_percent_mean_raw'] / cores, places=6)

    def test_sampling_exception_does_not_propagate(self):
        monitor = qdatamap.ResourceMonitor(interval=0.02)
        monitor.start()

        class BrokenProcess:
            def cpu_percent(self):
                raise RuntimeError('simulated sampling failure')

            def memory_info(self):
                raise RuntimeError('simulated sampling failure')

        # Break the process handle while the thread is running: the loop must
        # swallow the exception and stop() must still return the available data.
        monitor._process = BrokenProcess()
        time.sleep(0.2)
        metrics = monitor.stop()
        self.assertIsInstance(metrics, dict)
        self.assertIn('sampling_interval', metrics)
        self.assertIn('rss_start', metrics)

    def test_thread_is_daemon_and_terminates(self):
        monitor = qdatamap.ResourceMonitor(interval=0.05)
        monitor.start()
        self.assertIsNotNone(monitor._thread)
        self.assertTrue(monitor._thread.daemon)
        monitor.stop()
        monitor._thread.join(timeout=2)
        self.assertFalse(monitor._thread.is_alive())

    def test_start_failure_reports_gracefully(self):
        monitor = qdatamap.ResourceMonitor(interval=0.05)
        monitor._failed = True  # simulate psutil unavailable at start()
        metrics = monitor.stop()
        self.assertIsInstance(metrics, dict)
        self.assertEqual(metrics['samples_count'], 0)


if __name__ == '__main__':
    unittest.main()
