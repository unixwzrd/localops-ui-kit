from localops_ui import format_duration, format_number


def test_duration_formatting() -> None:
    assert format_duration(None) == "—"
    assert format_duration(0.25) == "250 ms"
    assert format_duration(65) == "1m 05s"
    assert format_duration(3660) == "1h 01m"


def test_number_formatting() -> None:
    assert format_number(None) == "—"
    assert format_number(1234.5) == "1,234.5"
    assert format_number(1.236, maximum_fraction_digits=2) == "1.24"
