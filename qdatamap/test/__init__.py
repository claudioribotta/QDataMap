# import qgis libs so that ve set the correct sip api version
try:
    import qgis   # pylint: disable=W0611  # NOQA
except ImportError:
    # Tests that do not need QGIS (Section 8.1 of the v1.1 plan) run against
    # stubbed qgis modules installed by qgis_stubs; tests that do need it
    # skip themselves.
    pass
