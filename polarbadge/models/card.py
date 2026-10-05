from base64 import b64encode
from decimal import Decimal
from pathlib import Path
from typing import Self, Literal


from pydantic import BaseModel, model_validator
from PIL import Image as PImage


SizeMM = Decimal
CSSOptions = dict[str, int|str]

class CardType(BaseModel):
    name: str
    width_mm: SizeMM
    height_mm: SizeMM
    width_px: int
    height_px: int

    @model_validator(mode='after')
    def check_portrait(self) -> Self:
        if self.width_mm > self.height_mm or self.width_px > self.height_px:
            raise ValueError(f"Card must be portrait (width cannot be larger than height)")
        return self


class ExternalFontFamily(BaseModel):
    path: str
    family_name: str

    @property
    def full_path(self) -> str:
        path = Path(self.path)
        return f"file://{path.absolute()}"


class Font(BaseModel):
    family: str | ExternalFontFamily
    size_pt: Decimal
    color: str = "ffffff"
    weight: int | None = None
    options: CSSOptions = {}

    @property
    def _family(self) -> str:
        return self.family.family_name if isinstance(self.family, ExternalFontFamily) else self.family

    @property
    def css(self) -> str:
        props = {
            "font-family": self._family,
            "color": f"#{self.color}",
            "font-size": f"{self.size_pt}pt"
        }
        if self.weight:
            props["font-weight"] = str(self.weight)

        props.update(self.options)

        return "; ".join([f"{k}: {v}" for k, v in props.items()])


class TextBox(BaseModel):
    width_mm: SizeMM
    height_mm: SizeMM
    anchor_x_mm: SizeMM
    anchor_y_mm: SizeMM
    align_x: Literal["left", "center", "right"] = "center"
    align_y: Literal["top", "middle", "bottom"] = "middle"
    font_override: Font | None = None
    fit_single_line: bool = False

    @property
    def css(self) -> str:
        props = {
            "width": f"{self.width_mm}mm",
            "height": f"{self.height_mm}mm",
            "top": f"{self.anchor_y_mm}mm",
            "left": f"{self.anchor_x_mm}mm",
            "text-align": self.align_x,
        }

        css_string = "; ".join([f"{k}: {v}" for k, v in props.items()])
        if self.font_override:
            css_string += "; " + self.font_override.css
        return css_string


class ImageBox(BaseModel):
    width_mm: SizeMM
    height_mm: SizeMM
    anchor_x_mm: SizeMM
    anchor_y_mm: SizeMM
    scaling: Literal["contain", "cover"] = "cover"


class Image(BaseModel):
    path: str
    pad_left_mm: Decimal | None = None
    pad_top_mm: Decimal | None = None


class Code2DBox(BaseModel):
    id_text_font: Font | None
    size_mm: SizeMM
    anchor_x_mm: SizeMM
    anchor_y_mm: SizeMM


class Design(BaseModel):
    card: CardType
    base_font: Font = Font(family="Arial", size_pt=24)
    orientation: Literal["portrait", "landscape"]
    background_color: str  = 'ffffff'  # hex code
    background_png: Image | None = None
    foreground_png: Image | None = None
    image_profile: ImageBox
    text_nick: TextBox
    text_name: TextBox
    text_crew: TextBox | None = None
    text_crew_name: TextBox | None = None
    code_2d_box: Code2DBox | None = None

    @model_validator(mode='after')
    def check_background_correct_size(self) -> Self:
        if self.background_png:
            image = PImage.open(self.background_png.path)
            width, height = image.size
            required_width, required_height = self.width_px, self.height_px
            if width != required_width or height != required_height:
                raise ValueError(
                    f"Size ({width}x{height}px) does not card requirements (must be "
                    f"{required_width}x{required_height}px)"
                )
        return self

    @model_validator(mode='after')
    def check_foreground_correct_size(self) -> Self:
        if self.foreground_png:
            image = PImage.open(self.foreground_png.path)
            width, height = image.size
            required_width, required_height = self.width_px, self.height_px
            if width != required_width or height != required_height:
                raise ValueError(
                    f"Size ({width}x{height}px) does not card requirements (must be "
                    f"{required_width}x{required_height}px)"
                )
        return self

    # Calculated properties based on orientation
    # The card specs are based on portrait orientation, so landscape switches the two around
    @property
    def is_portrait(self) -> bool:
        return self.orientation == "portrait"

    @property
    def width_mm(self) -> SizeMM:
        return self.card.width_mm if self.is_portrait else self.card.height_mm

    @property
    def height_mm(self) -> SizeMM:
        return self.card.height_mm if self.is_portrait else self.card.width_mm

    @property
    def width_px(self) -> int:
        return self.card.width_px if self.is_portrait else self.card.height_px

    @property
    def height_px(self) -> int:
        return self.card.height_px if self.is_portrait else self.card.width_px

    @property
    def background_b64(self) -> str | None:
        if self.background_png:
            with open(self.background_png.path, "br") as f:
                return b64encode(f.read()).decode("utf-8")

    @property
    def foreground_b64(self) -> str| None:
        if self.foreground_png:
            with open(self.foreground_png.path, "br") as f:
                return b64encode(f.read()).decode("utf-8")

    def get_external_fonts(self) -> list[ExternalFontFamily]:
        # Path to all the potential fonts we have
        font_paths = [
            "base_font",
            "text_nick.font_override",
            "text_name.font_override",
            "text_crew.font_override",
            "text_crew_name.font_override",
            "code_2d_box.id_text_font",
        ]
        found_fonts = {}
        for path in font_paths:
            parts = path.split(".")
            part = parts.pop(0)
            item = getattr(self, part, None)
            for part in parts:
                item = getattr(item, part, None)
                if isinstance(item, Font) and isinstance(item.family, ExternalFontFamily):
                    font = item.family
                    if font.family_name in found_fonts and font != found_fonts[font.family_name]:
                        print(f"Error: font family name '{font}' is already used. Skipping font for {path} in design")
                        continue
                    found_fonts[font.family_name] = font

        return list(found_fonts.values())