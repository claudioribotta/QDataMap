QDataMap - QGIS plugin
======================

QDataMap iteratively prints geospatially explicit tabular datasets with which
a set of polygons can be associated. See metadata.txt for version, license
(GPL-3) and links to the issue tracker and repository.

Target environment
------------------

QDataMap v1.1 is bound to QGIS 3.40 LTR (validated on 3.40.15). The Python
dependencies are pinned to exact versions, verified at runtime, and listed in
requirements.txt; requirements-paper.txt is the frozen record of the
environment used to produce the results reported in the accompanying
manuscript. No package is ever installed without explicit user confirmation.

Every run writes the resolved environment into the generated QGIS project
metadata (scope "QDataMap") and produces a QDataMap_run_report.txt next to
its outputs; batch runs additionally produce a QDataMap_batch_report.txt in
the output root folder.

Running the tests
-----------------

From the parent folder of the plugin directory, run:

    python -m unittest discover -s qdatamap/test -t .

Use the Python bundled with QGIS (e.g. on Windows
"C:\Program Files\QGIS 3.40.15\bin\python-qgis-ltr.bat") to run the full
suite; with a plain Python interpreter the QGIS-dependent tests skip
themselves and only the environment-independent tests run.
