import pytest

from trace_file_convert import TraceFileConverter


@pytest.fixture(scope="class")
def converter():
    """Fixture for an instance of the TraceFileConverter.

    Yields
    ------
    An instance of TraceFileConverter.
    """
    yield TraceFileConverter()


def test_import(converter: TraceFileConverter):
    pass


def test_export(converter: TraceFileConverter):
    pass


def test_convert_xml(converter: TraceFileConverter):
    pass


def test_convert_stp(converter: TraceFileConverter):
    pass


def test_convert_colors(converter: TraceFileConverter):
    pass


def test_get_plot_data(converter: TraceFileConverter):
    pass


def test_as_cli():
    pass
