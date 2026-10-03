"""DEF-011 regression: the build must reject placeholder assets, not just absent ones.

Before the fix, scripts/build.py precondition 4 checked only that
packaging/icons/app.ico and packaging/templates/FPAMonthEndCopilot_v1.pptx
existed. Both were ASCII placeholder files - 15 bytes of "ICO_PLACEHOLDER" and
16 bytes of "PPTX_PLACEHOLDER" - so they satisfied doc 15 section 3.1 #4 and
shipped inside the installer.

Precondition 4b now validates the assets. These tests pin that behaviour,
including the positive path so the gate cannot rot into always-fail.
"""
import importlib.util
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_build_module():
    """Import scripts/build.py without executing its CLI entrypoint."""
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("buildmod_def011", ROOT / "scripts" / "build.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["buildmod_def011"] = module
    spec.loader.exec_module(module)
    return module


build = _load_build_module()


def _write_ico(path: Path, images: int = 3) -> Path:
    """A structurally valid ICO: correct header plus enough bulk to clear the size floor."""
    header = (0).to_bytes(2, "little") + (1).to_bytes(2, "little") + images.to_bytes(2, "little")
    entry_size = 40
    body = b"\x00" * (entry_size * images)
    path.write_bytes(header + body + b"\x00" * build.MIN_ICO_BYTES)
    return path


def _write_pptx(path: Path, layouts=None) -> Path:
    """A ZIP that mimics a minimal OOXML package carrying the required layout names."""
    layouts = layouts if layouts is not None else build.REQUIRED_PPTX_LAYOUTS
    filler = "<p:spTree>" + "<p:sp/>" * 400
    with zipfile.ZipFile(path, "w") as zf:
        for i, name in enumerate(layouts, start=1):
            zf.writestr(
                f"ppt/slideLayouts/slideLayout{i}.xml",
                f'<p:sldLayout name="{name}">{filler}</p:sldLayout>',
            )
        zf.writestr("[Content_Types].xml", "<Types/>" * 400)
        zf.writestr("ppt/presentation.xml", "<p:presentation/>" * 200)
    return path


def test_placeholder_text_file_is_not_a_valid_ico(tmp_path):
    stub = tmp_path / "app.ico"
    stub.write_bytes(b"ICO_PLACEHOLDER")
    assert build._is_valid_ico(stub) is False


def test_truncated_ico_with_valid_header_is_still_rejected(tmp_path):
    """Header alone is not enough - the size floor must reject a stub."""
    stub = tmp_path / "app.ico"
    stub.write_bytes((0).to_bytes(2, "little") + (1).to_bytes(2, "little") + (1).to_bytes(2, "little"))
    assert build._is_valid_ico(stub) is False


def test_wrong_ico_type_is_rejected(tmp_path):
    """type=2 is a cursor, not an icon."""
    bad = tmp_path / "app.ico"
    bad.write_bytes((0).to_bytes(2, "little") + (2).to_bytes(2, "little") + (1).to_bytes(2, "little") + b"\x00" * 2000)
    assert build._is_valid_ico(bad) is False


def test_valid_ico_is_accepted(tmp_path):
    assert build._is_valid_ico(_write_ico(tmp_path / "app.ico")) is True


def test_missing_ico_is_rejected(tmp_path):
    assert build._is_valid_ico(tmp_path / "nope.ico") is False


def test_placeholder_text_file_is_not_a_valid_pptx(tmp_path):
    """The exact 16-byte artefact that shipped."""
    stub = tmp_path / "t.pptx"
    stub.write_bytes(b"PPTX_PLACEHOLDER")
    with pytest.raises(build.BuildError, match="not a real .pptx"):
        build._validate_pptx_template(stub)


def test_pptx_missing_a_required_layout_is_rejected(tmp_path):
    """Doc 12 3.6 requires all seven; a partial set must not pass."""
    partial = list(build.REQUIRED_PPTX_LAYOUTS)[:-1]
    path = _write_pptx(tmp_path / "partial.pptx", layouts=partial)
    with pytest.raises(build.BuildError, match="FPA-PPT-DISCLAIMER"):
        build._validate_pptx_template(path)


def test_pptx_with_wrong_layout_names_is_rejected(tmp_path):
    path = _write_pptx(tmp_path / "bogus.pptx", layouts=["Title Only"] * 7)
    with pytest.raises(build.BuildError, match="doc 12 section 3.6 requires layouts"):
        build._validate_pptx_template(path)


def test_conforming_pptx_is_accepted(tmp_path):
    """Positive control - the gate must be able to pass a real template."""
    build._validate_pptx_template(_write_pptx(tmp_path / "good.pptx"))


def test_missing_pptx_is_rejected(tmp_path):
    with pytest.raises(build.BuildError, match="missing"):
        build._validate_pptx_template(tmp_path / "absent.pptx")


def test_required_layout_names_match_doc_12_contract():
    assert build.REQUIRED_PPTX_LAYOUTS == (
        "FPA-PPT-001", "FPA-PPT-002", "FPA-PPT-003",
        "FPA-PPT-004", "FPA-PPT-005", "FPA-PPT-006",
        "FPA-PPT-DISCLAIMER",
    )