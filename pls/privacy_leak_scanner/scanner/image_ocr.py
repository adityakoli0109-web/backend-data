from pathlib import Path
from PIL import Image, ImageOps
import pytesseract


def _configure_tesseract() -> None:
    configured = getattr(pytesseract.pytesseract, "tesseract_cmd", "")
    if configured and configured != "tesseract":
        return
    for path in (
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ):
        if path.exists():
            pytesseract.pytesseract.tesseract_cmd = str(path)
            return


def extract_text_from_image(path: Path) -> str:
    _configure_tesseract()
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        return pytesseract.image_to_string(image)
