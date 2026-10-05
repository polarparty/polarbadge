from io import BytesIO
from typing import Any
from base64 import b64encode

import requests
from PIL import ImageFont, ImageOps
from jinja2 import Environment, PackageLoader, select_autoescape
from treepoem import generate_barcode

from polarbadge.models.card import Design, ExternalFontFamily


env = Environment(
    loader=PackageLoader("polarbadge"),
    autoescape=select_autoescape()
)

template = env.get_template("card.html.j2")

def render_to_string(context: dict[str, Any]) -> str:
    return template.render(**context)


def _get_picture(url):
    headers = {
        "User-Agent": "Badgerizer 0.1"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.content


def _fit_font_size(text, font, width_mm):
    font_size_pt = float(font.size_pt)
    if not text or not isinstance(font.family, ExternalFontFamily):
        return font_size_pt

    font_size_px = max(1, round(font_size_pt * 300 / 72))
    measured_font = ImageFont.truetype(font.family.path, font_size_px)
    try:
        axes = measured_font.get_variation_axes()
    except OSError:
        axes = []
    if axes:
        variation_values = [
            font.weight if axis["name"] == b"Weight" and font.weight is not None else axis["default"]
            for axis in axes
        ]
        measured_font.set_variation_by_axes(variation_values)

    text_width_px = measured_font.getlength(text)
    available_width_px = float(width_mm) * 300 / 25.4
    return round(min(font_size_pt, font_size_pt * available_width_px / text_width_px * 0.98), 2)


def render_card(
        design: Design,
        nick: str,
        name: str,
        crew: str,
        user_id: int,
        profile_picture_path: str | None = None,
        profile_picture_content: bytes | None = None,
        debug: bool = False
) -> str:

    if profile_picture_path:
        if profile_picture_path.startswith("http"):
            pic = _get_picture(profile_picture_path)
        else:
            with open(profile_picture_path, "b") as f:
                pic = f.read()
        pic_b64 = b64encode(pic).decode("utf-8")
    elif profile_picture_content:
        pic_b64 = b64encode(profile_picture_content).decode("utf-8")
    else:
        pic_b64 = None

    context = {
        "design": design,
        "card": design.card,
        "userid": user_id,
        "subject": {
            "user_id": user_id,
            "name": name,
            "nick": nick,
            "crew": crew,
            "pic_b64": pic_b64
        },
        "debug": debug
    }

    if design.code_2d_box:
        code_img = generate_barcode("datamatrix", str(user_id), scale=4)
        code_img = ImageOps.expand(code_img, border=10, fill="white")

        buffer = BytesIO()
        code_img.save(buffer, format="PNG")
        code_b64 = b64encode(buffer.getvalue()).decode("utf-8")
        context["subject"]["code_b64"] = code_b64

    if design.text_nick.fit_single_line:
        context["subject"]["nick_font_size"] = _fit_font_size(
            nick,
            design.text_nick.font_override or design.base_font,
            design.text_nick.width_mm
        )

    if design.text_crew_name and design.text_crew_name.font_override:
        context["subject"]["crew_font_size"] = _fit_font_size(
            crew,
            design.text_crew_name.font_override,
            design.text_crew_name.width_mm
        )

    return render_to_string(context)        


def render_to_image(path, design, html) -> None:
    # canvas = plutoprint.ImageCanvas.create_for_data(
    #     memoryview(html.encode("utf-8")),
    #     width_px,
    #     height_px
    # )
    # canvas.write_to_png(path)

    # book = plutoprint.Book(
    #     size=plutoprint.PageSize(
    #         float(width_mm) * plutoprint.UNITS_MM,
    #         float(height_mm) * plutoprint.UNITS_MM
    #     ),
    #     media=plutoprint.MEDIA_TYPE_PRINT
    # )
    # book.load_html(html)
    # book.write_to_png(path, width_px, height_px)

    from weasyprint import HTML
    from pdf2image import convert_from_path
    from PIL import Image
    data = HTML(string=html)
    pdf_buffer = BytesIO()
    data.write_pdf("/tmp/tmp.pdf")

    image = convert_from_path("/tmp/tmp.pdf", dpi=300)[0]
    if design.is_portrait:
        image = image.transpose(Image.ROTATE_90)
    image.convert("RGB")
    image.save(path, "BMP")
