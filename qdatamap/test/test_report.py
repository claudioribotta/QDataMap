# coding=utf-8
"""Tests for the run/batch report builders (Sections 6-7 of the v1.1 plan).

Runnable without QGIS: the builders are pure text construction.
"""

import os
import tempfile
import unittest

from .qgis_stubs import load_plugin_module

qdatamap = load_plugin_module()


def fixture_environment():
    return {
        'timestamp': '2026-07-31T10:00:00+02:00',
        'plugin_version': '1.1',
        'qgis_version': '3.40.15-Bratislava',
        'qgis_ltr_target': '3.40',
        'dependencies_resolved': {pkg: ver for pkg, ver
                                  in qdatamap.PINNED_DEPENDENCIES.items()},
        'dependencies_pinned': dict(qdatamap.PINNED_DEPENDENCIES),
        'environment_matches_pin': True,
        'os': 'Windows-11-10.0.26200-SP0',
        'python_version': '3.12.6',
        'processor': 'Intel64 Family 6 Model 154',
        'cpu_cores_physical': 8,
        'cpu_cores_logical': 16,
        'cpu_freq_max_mhz': 3200.0,
        'ram_total_bytes': 34359738368,
    }


def fixture_run_metrics():
    return {
        'environment': fixture_environment(),
        'input': {
            'shape_path': 'C:/data/comuni.gpkg',
            'shape_name': 'comuni.gpkg',
            'shape_size': 1048576,
            'shape_mtime': '2026-07-01T09:00:00+02:00',
            'csv_path': 'C:/data/popolazione.csv',
            'csv_name': 'popolazione.csv',
            'csv_size': 20480,
            'csv_mtime': '2026-07-02T09:00:00+02:00',
            'csv_encoding': 'utf-8',
            'csv_delimiter': ';',
            'input_crs': 'EPSG:32632',
            'project_crs': 'EPSG:3857',
        },
        'parameters': {
            'select_render_methods': 'Graduated',
            'popolazione_città': 'sì',  # non-ASCII name and value
            'insert_chart_checkbox': True,
        },
        'join': {
            'shape_features_total': 100,
            'csv_records_total': 95,
            'shape_matched': 90,
            'shape_unmatched': 10,
            'csv_matched': 92,
            'csv_unmatched': 3,
            'output_features': 92,
            'input_vertices_total': 5200,
            'output_vertices_total': 5350,
            'duplicate_geometries': 2,
            'discard_nonmatching': True,
            'matched_null_values': 4,
            'matched_zero_values': 7,
            'renderer_classes': 5,
        },
        'performance': {
            'wall_time': 2.345,
            't_join_stats': 0.111,
            't_join': 0.789,
            't_rendering': 1.234,
            't_export': 0.321,
            't_report': 0.012,
            'cpu_percent_peak_raw': 380.0,
            'cpu_percent_mean_raw': 120.5,
            'cpu_percent_peak_normalized': 23.75,
            'cpu_percent_mean_normalized': 7.53,
            'cpu_logical_cores': 16,
            'samples_count': 12,
            'sampling_interval': 0.2,
            'rss_start': 500000000,
            'rss_peak': 650000000,
            'rss_delta': 150000000,
            'output_sizes': {'out.gpkg': 2000000, 'out.qgz': 30000, 'out.png': 500000},
            'output_total_bytes': 2530000,
            'input_total_bytes': 1069056,
            'output_input_ratio': 2.366,
        },
        'outcome': 'success',
    }


def fixture_batch_metrics(stopped=False):
    per_file = []
    for i in (1, 2, 3):
        per_file.append({
            'iteration': i,
            'file_name': f'file_{i}.csv',
            'outcome': 'success' if i != 2 else 'failed',
            'matched_features': 90,
            'unmatched_features': 10,
            'null_values': 4,
            'output_vertices': 5350,
            'classes': 5,
            'wall_time_s': 2.0 + i,
            't_join_s': 0.5,
            't_rendering_s': 1.0,
            't_export_s': 0.3,
            'rss_peak_bytes': 600000000 + i,
            'cpu_mean_pct': 100.0,
            'cpu_peak_pct': 350.0,
            'output_size_bytes': 2500000,
        })
    return {
        'environment': fixture_environment(),
        'scope': {
            'csv_folder': 'C:/data/csv',
            'output_root': 'C:/output',
            'shape_path': 'C:/data/comuni.gpkg',
            'csv_found': 3,
            'csv_processed': 3,
            'csv_succeeded': 2,
            'csv_failed': 1,
            'stopped_by_user': stopped,
            'schema_validation': 'passed',
            'schema_nonconforming': None,
            'prelim_stats_enabled': False,
        },
        'parameters': {'select_render_methods': 'Categorized'},
        'per_file': per_file,
        'aggregate': {
            'batch_wall_time': 9.5,
            'throughput_maps_per_minute': 18.9,
            'map_time_mean': 4.0,
            'map_time_median': 4.0,
            'map_time_min': 3.0,
            'map_time_max': 5.0,
            'map_time_std': 1.0,
            'phase_join_mean': 0.5,
            'phase_rendering_mean': 1.0,
            'phase_export_mean': 0.3,
            'cpu_percent_mean_raw': 110.0,
            'cpu_percent_peak_raw': 390.0,
            'cpu_percent_mean_normalized': 6.9,
            'cpu_percent_peak_normalized': 24.4,
            'samples_count': 48,
            'sampling_interval': 0.2,
            'rss_start': 500000000,
            'rss_peak': 700000000,
            'rss_end': 510000000,
            'input_total_bytes': 1100000,
            'output_total_bytes': 7500000,
            'output_mean_bytes': 2500000,
        },
    }


class TestRunReport(unittest.TestCase):

    def test_contains_all_mandatory_fields(self):
        text = qdatamap.build_run_report(fixture_run_metrics())
        # Section 1 - Environment
        for label in ('Timestamp:', 'Plugin version: 1.1',
                      'QGIS version: 3.40.15-Bratislava', 'QGIS LTR target: 3.40',
                      'Dependencies (resolved):', 'Dependencies (pinned):',
                      'Environment matches pin: true', 'Operating system:',
                      'Python version:', 'Processor:', 'CPU cores (physical): 8',
                      'CPU cores (logical): 16', 'CPU nominal frequency (MHz):',
                      'Total system RAM:'):
            self.assertIn(label, text)
        for pkg, ver in qdatamap.PINNED_DEPENDENCIES.items():
            self.assertIn(f'{pkg}: {ver}', text)
        # Section 2 - Input
        for label in ('Geospatial layer path:', 'Geospatial layer name:',
                      'Geospatial layer size:', 'Geospatial layer mtime:',
                      'CSV path:', 'CSV name:', 'CSV size:', 'CSV mtime:',
                      'CSV detected encoding: utf-8', 'CSV detected delimiter: ;',
                      'Input layer CRS: EPSG:32632', 'Project CRS applied: EPSG:3857'):
            self.assertIn(label, text)
        # Section 3 - Parameters
        self.assertIn('select_render_methods = Graduated', text)
        self.assertIn('insert_chart_checkbox = true', text)
        # Section 4 - Join and output metrics
        for label in ('Geospatial features (total): 100',
                      'Geospatial vertices (total): 5200',
                      'CSV records (total): 95',
                      'Geospatial features matched: 90',
                      'Geospatial features unmatched: 10',
                      'CSV records matched: 92', 'CSV records unmatched: 3',
                      'Output features after join: 92',
                      'Output vertices after join: 5350',
                      'Duplicate geometries from multiple matches: 2',
                      'Discard nonmatching records: true',
                      'Matched features with NULL mapped value: 4',
                      'Matched features with zero mapped value: 7',
                      'Renderer classes produced: 5'):
            self.assertIn(label, text)
        # Section 5 - Performance
        for label in ('Wall time (s): 2.345', 'Phase join_stats (s): 0.111',
                      'Phase join (s): 0.789', 'Phase rendering (s): 1.234',
                      'Phase export (s): 0.321', 'Phase report (s): 0.012',
                      'CPU peak, raw sum over cores (%): 380.0',
                      'CPU mean, raw sum over cores (%): 120.5',
                      'CPU peak, normalized over logical cores (%): 23.75',
                      'CPU mean, normalized over logical cores (%): 7.53',
                      'Resource samples collected: 12',
                      'Resource sampling interval (s): 0.2',
                      'Process RSS at start:', 'Process RSS peak:',
                      'Process RSS delta (peak - start):', 'Output file sizes:',
                      'Total output size:', 'Total input size:',
                      'Output/input size ratio: 2.366'):
            self.assertIn(label, text)

    def test_utf8_file_survives_non_ascii_field_names(self):
        text = qdatamap.build_run_report(fixture_run_metrics())
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'QDataMap_run_report.txt')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write(text)
            with open(path, encoding='utf-8') as handle:
                readback = handle.read()
        self.assertIn('popolazione_città = sì', readback)

    def test_missing_values_render_as_not_available(self):
        text = qdatamap.build_run_report({})
        for label in ('QGIS version: not available',
                      'Environment matches pin: not available',
                      'CSV detected encoding: not available',
                      'Renderer classes produced: not available',
                      'Wall time (s): not available',
                      'Process RSS peak: not available',
                      'Output/input size ratio: not available'):
            self.assertIn(label, text)

    def test_empty_metrics_do_not_raise(self):
        qdatamap.build_run_report(None)
        qdatamap.build_run_report({})
        qdatamap.build_run_report({'environment': None, 'performance': {}})


class TestBatchReport(unittest.TestCase):

    def test_contains_all_mandatory_fields(self):
        text = qdatamap.build_batch_report(fixture_batch_metrics())
        for label in ('Input CSV folder:', 'Output root folder:',
                      'Geospatial layer:', 'CSV files found: 3',
                      'CSV files processed: 3', 'CSV files succeeded: 2',
                      'CSV files failed: 1',
                      'Batch interrupted with Stop button: false',
                      'CSV schema consistency validation: passed',
                      'Preliminary join statistics enabled: false',
                      'Batch wall time (s): 9.500',
                      'Throughput (maps/minute): 18.9',
                      'Time per map, mean (s):', 'Time per map, median (s):',
                      'Time per map, min (s):', 'Time per map, max (s):',
                      'Time per map, standard deviation (s):',
                      'Mean phase time, join (s):',
                      'Mean phase time, rendering (s):',
                      'Mean phase time, export (s):',
                      'CPU mean over the whole batch, raw (%):',
                      'CPU peak over the whole batch, raw (%):',
                      'Resource sampling interval (s): 0.2',
                      'Batch RSS initial:', 'Batch RSS peak:', 'Batch RSS final:',
                      'Total input size:', 'Total output size:',
                      'Mean output size per map:'):
            self.assertIn(label, text)

    def test_per_file_table_has_consistent_column_count(self):
        text = qdatamap.build_batch_report(fixture_batch_metrics())
        lines = text.splitlines()
        header_index = lines.index('\t'.join(qdatamap.BATCH_TABLE_COLUMNS))
        n_columns = len(qdatamap.BATCH_TABLE_COLUMNS)
        table_rows = []
        for line in lines[header_index + 1:]:
            if not line.strip():
                break
            table_rows.append(line)
        self.assertEqual(len(table_rows), 3)
        for row in table_rows:
            self.assertEqual(len(row.split('\t')), n_columns,
                             f'wrong column count in row: {row!r}')

    def test_failed_row_pads_missing_cells(self):
        metrics = fixture_batch_metrics()
        metrics['per_file'].append({'iteration': 4, 'file_name': 'bad.csv',
                                    'outcome': 'failed'})
        text = qdatamap.build_batch_report(metrics)
        failed_row = [line for line in text.splitlines()
                      if line.startswith('4\tbad.csv')][0]
        self.assertEqual(len(failed_row.split('\t')),
                         len(qdatamap.BATCH_TABLE_COLUMNS))
        self.assertIn('not available', failed_row)

    def test_interrupted_batch_still_reports_with_flag(self):
        metrics = fixture_batch_metrics(stopped=True)
        metrics['scope']['csv_processed'] = 2
        text = qdatamap.build_batch_report(metrics)
        self.assertIn('Batch interrupted with Stop button: true', text)
        self.assertIn('Files completed before interruption: 2 of 3', text)

    def test_empty_metrics_do_not_raise(self):
        qdatamap.build_batch_report(None)
        qdatamap.build_batch_report({})


if __name__ == '__main__':
    unittest.main()
