from qtpy.QtCore import Qt


def test_curves_model_qtmodeltester(qtmodeltester, qtrace):
    """Check the validity of the ArchiverCurveModel with pytest-qt

    Parameters
    ----------
    qtmodeltester : fixture
        pytest-qt fixture used for testing the validity of AbstractItemModels
    qtrace : fixture
        Instance of TraceDisplay for application testing

    Expectations
    ------------
    qtmodeltester finds no issues with the model
    """
    qtmodeltester.check(qtrace.curves_model, force_py=True)


def test_default_curve(qtrace):
    """Check default values for curve as represented in the table model"""
    curves_model = qtrace.curves_model

    row_actual = []
    row_expected = ["", Qt.Checked, Qt.Checked, "", "#008cf9", "Axis 1",
                    "Direct", "Solid", "1px", "None", "10px", Qt.Checked, None]  # fmt: skip

    for col in range(curves_model.columnCount()):
        index = curves_model.index(0, col)
        role = Qt.CheckStateRole if col in curves_model.checkable_cols else Qt.DisplayRole
        data = curves_model.data(index, role)
        row_actual.append(data)

    assert row_actual == row_expected


def test_contains(qtrace):
    pass


def test_append_curve(qtrace):
    pass


def test_remove_curve(qtrace):
    pass


def test_set_model_curves(qtrace):
    pass


def test_alter_curve_data(qtrace):
    pass


def test_convert_curve_to_formula(qtrace):
    pass


def test_convert_formula_to_curve(qtrace):
    pass


def test_invalid_formula(qtrace):
    pass


def test_recursive_formula(qtrace):
    pass


def test_next_header(qtrace):
    pass


def test_live_connection_status(qtrace):
    pass


def test_archive_connection_status(qtrace):
    pass


def test_set_axis_from_unit(qtrace):
    """Check that when a curve's units change, the curve is moved to an axis
    that reflects the new units.
    """
    pass
