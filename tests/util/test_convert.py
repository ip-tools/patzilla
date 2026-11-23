from typing import Generator

import pytest
from PIL import Image, ImageDraw
from pathlib import Path

from patzilla.util.image.convert import to_png, to_pdf, png_resize, pdf_join, pdf_make_metadata, pdf_set_metadata


@pytest.fixture
def tiff(tmp_path) -> Generator[Path, None, None]:
    """Provide a dummy image in TIFF format."""
    path = tmp_path / "test.tiff"
    with Image.new(mode="RGB", size=(25, 25)) as img:
        draw = ImageDraw.Draw(img)
        draw.line((0, 0) + img.size, fill=128)
        img.save(path)
    yield path


def test_to_png(tiff):
    """Test converting to PNG."""
    png = to_png(tiff)
    assert png.read(20).startswith(b"\x89PNG")


def test_to_pdf(tiff):
    """Test converting to PDF."""
    pdf = to_pdf(tiff)
    assert pdf.read(20).startswith(b"%PDF-1.4")


def test_png_resize(tiff):
    """Test resizing PNG."""
    png = to_png(tiff)
    png = png_resize(png, 42)
    assert png[:20].startswith(b"\x89PNG")


def test_pdf_join(tiff):
    """Test joining PDFs."""
    pdf_single = to_pdf(tiff).read()
    pdf = pdf_join([pdf_single, pdf_single])
    assert pdf[:20].startswith(b"%PDF-1.4")


def test_pdf_set_metadata(tiff):
    """Test setting PDF metadata."""
    pdf = to_pdf(tiff)
    metadata = pdf_make_metadata("title", 'ip-navigator:digi42', 42, None)
    pdf = pdf_set_metadata(pdf.read(), metadata)
    assert pdf[:20].startswith(b"%PDF-1.4")
