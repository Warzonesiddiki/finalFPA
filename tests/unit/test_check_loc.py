"""Unit test for scripts/check_loc.py (TB-029)."""

from scripts.check_loc import check_line_counts


def test_check_line_counts_pass(tmp_path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    small_file = app_dir / "small.py"
    small_file.write_text("print('hello')\n")

    res = check_line_counts(app_dir)
    assert res == 0


def test_check_line_counts_fail_unjustified(tmp_path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    big_file = app_dir / "big.py"
    big_file.write_text("x = 1\n" * 501)

    res = check_line_counts(app_dir)
    assert res == 1


def test_check_line_counts_pass_justified(tmp_path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    big_file = app_dir / "big.py"
    big_file.write_text('"""Justification: long file for test."""\n' + "x = 1\n" * 501)

    res = check_line_counts(app_dir)
    assert res == 0
