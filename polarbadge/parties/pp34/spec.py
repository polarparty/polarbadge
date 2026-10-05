import os

from polarbadge.card.constants import CARD_TYPES
from polarbadge.models.card import Font, TextBox, Image, ImageBox, Design, ExternalFontFamily

# Dir or current file
BASE_PATH = os.path.dirname(os.path.realpath(__file__))

FONT_QUICKSAND = ExternalFontFamily(
    family_name="Quicksand",
    path=os.path.join(BASE_PATH, "fonts/Quicksand/Quicksand-VariableFont_wght.ttf")
)

FONT_ETHNOCENTRIC = ExternalFontFamily(
    family_name="Ethnocentric",
    path=os.path.join(BASE_PATH, "fonts/Ethnocentric/Ethnocentric-Regular.otf")
)


design = Design(
    card=CARD_TYPES["cr80"],
    base_font=Font(
        family=FONT_QUICKSAND,
        size_pt=18,
        color="ffffff"
    ),
    orientation="portrait",
    background_png=Image(path=os.path.join(BASE_PATH, "background.png")),
    #foreground_png=Image(path=os.path.join(BASE_PATH, "foreground.png")),
    image_profile=ImageBox(
        width_mm="18.54",
        height_mm="18.54",
        anchor_x_mm="7.03",
        anchor_y_mm="41.10"
    ),
    text_nick=TextBox(
        width_mm="25.5",
        height_mm="5.0",
        anchor_x_mm="27.35",
        anchor_y_mm="42.30",
        align_x="left",
        fit_single_line=True,
        font_override=Font(
            family=FONT_QUICKSAND,
            size_pt="13",
            color="ffffff"
        )
    ),
    text_name=TextBox(
        width_mm="25.5",
        height_mm="12.0",
        anchor_x_mm="27.35",
        anchor_y_mm="48.70",
        align_x="left",
        font_override=Font(
            family=FONT_QUICKSAND,
            size_pt="8",
            color="ffffff"
        )
    ),
    text_crew_name=TextBox(
        width_mm="46.186",
        height_mm="6.0",
        anchor_x_mm="4.0",
        anchor_y_mm="78.0",
        font_override=Font(
            family=FONT_ETHNOCENTRIC,
            size_pt="14",
            color="ffffff"
        )
    )
)
