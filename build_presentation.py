"""Build a Latin Exclusive property presentation from the Par208 reference PDF.

The reference PDF is used as the template: logo, colours, icons, overlays and
the contact page are kept as-is; only photos and property texts are replaced.

Usage:
    python3 build_presentation.py <reference.pdf> <photos_dir> <fonts_dir> <out.pdf> <properties/xxx.py>
"""
import io
import sys

import pymupdf as fitz
from PIL import Image

REF, PHOTOS, FONTS, OUT, CONFIG = sys.argv[1:6]

NAVY = 0x2C3149
RED = 0xC13832
GREY = 0x949FB7
WHITE = 0xFFFFFF

# ---------------------------------------------------------------- content
# property texts and photo layout live in properties/<code>.py
TERMS, TERMS_NOTE, FOCUS = [], "", {}
exec(open(CONFIG, encoding="utf-8").read())


# ---------------------------------------------------------------- helpers
def photo_bytes(pid, aspect, max_w=1600):
    """Centre-crop photo `pid` to `aspect` (w/h) and return JPEG bytes."""
    im = Image.open(f"{PHOTOS}/{pid}.jpg").convert("RGB")
    w, h = im.size
    if w / h > aspect:  # too wide -> crop sides
        nw = round(h * aspect)
        x0 = round((w - nw) * FOCUS.get(pid, 0.5))
        im = im.crop((x0, 0, x0 + nw, h))
    else:               # too tall -> crop top/bottom
        nh = round(w / aspect)
        y0 = (h - nh) // 2
        im = im.crop((0, y0, w, y0 + nh))
    if im.width > max_w:
        im = im.resize((max_w, round(max_w * im.height / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84, optimize=True)
    return buf.getvalue()


def replace(page, doc, xref, pid, max_w=1600):
    info = doc.extract_image(xref)
    page.replace_image(xref, stream=photo_bytes(pid, info["width"] / info["height"], max_w))


FONT_FILES = {
    "osl": "OpenSans-Light.ttf",
    "osr": "OpenSans-Regular.ttf",
    "oss": "OpenSans-SemiBold.ttf",
    "osb": "OpenSans-Bold.ttf",
}
FONTS_OBJ = {k: fitz.Font(fontfile=f"{FONTS}/{v}") for k, v in FONT_FILES.items()}


def add_fonts(page):
    for k, v in FONT_FILES.items():
        page.insert_font(fontname=k, fontfile=f"{FONTS}/{v}")


def text(page, x, y, s, font, size, color):
    page.insert_text((x, y), s, fontname=font, fontsize=size,
                     color=fitz.sRGB_to_pdf(color))
    return x + FONTS_OBJ[font].text_length(s, size)


def erase_text(page, rects):
    for r in rects:
        page.add_redact_annot(fitz.Rect(r), fill=False)
    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                          graphics=fitz.PDF_REDACT_LINE_ART_NONE)


def wrap(s, font, size, width):
    lines, cur = [], ""
    for word in s.split():
        trial = (cur + " " + word).strip()
        if FONTS_OBJ[font].text_length(trial, size) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


# ---------------------------------------------------------------- build
order = [0, 1, 2] + [g[0] for g in GALLERY] + [7]
doc = fitz.open()
for pno in order:
    src = fitz.open(REF)          # fresh source -> independent image objects
    doc.insert_pdf(src, from_page=pno, to_page=pno)
    src.close()

# 1 - cover (image object shared with page 2)
p = doc[0]
replace(p, doc, p.get_images()[0][0], COVER_PHOTO, max_w=2000)
erase_text(p, [(240, 231, 480, 243)])
add_fonts(p)
parts = [(CODE, "oss", WHITE), (" ", "osl", WHITE), ("|", "osl", GREY),
         (" ", "osl", WHITE), (TITLE, "osl", WHITE)]
total = sum(FONTS_OBJ[f].text_length(s, 11) for s, f, _ in parts)
x = 360 - total / 2
for s, f, c in parts:
    x = text(p, x, 240.6, s, f, 11, c)

# 2 - main photo, location, rooms box
p = doc[1]
img = [i[0] for i in p.get_images() if i[2] == 1280][0]
if doc.extract_image(img)["width"] == 1280:   # not already replaced via page 1
    replace(p, doc, img, COVER_PHOTO, max_w=2000)
erase_text(p, [(600, 182, 715, 195), (600, 209, 715, 221),
               (543, 341, 590, 350), (639, 341, 653, 350)])
add_fonts(p)
text(p, 603.8, 192.9, CODE, "osb", 11, NAVY)
text(p, 603.8, 219.0, DISTRICT, "osr", 10, NAVY)
ty = 243.0
for label, value in TERMS:
    text(p, 603.8, ty, label, "osl", 8.5, NAVY)
    text(p, 603.8, ty + 11, value, "osb", 8.5, NAVY)
    ty += 26
if TERMS_NOTE:
    text(p, 603.8, ty - 4, TERMS_NOTE, "osl", 7.5, GREY)
x = text(p, 544.3, 348.6, BATHROOMS + " ", "osb", 8, WHITE)
text(p, x, 348.6, "bathrooms", "osr", 8, WHITE)
# keep "m²" in place: right-align the number to where "209" ended
num_w = FONTS_OBJ["osb"].text_length(AREA, 8)
text(p, 652.6 - num_w, 348.6, AREA, "osb", 8, WHITE)

# 3 - key features
p = doc[2]
replace(p, doc, [i[0] for i in p.get_images() if i[2] == 1280][0], FEATURE_PHOTO)
erase_text(p, [(505, 99, 715, 345)])
add_fonts(p)
LEFT, WIDTH, LH, SIZE = 509.9, 188, 12, 10
y = 108.9
for line in wrap(DESCRIPTION, "osl", SIZE, WIDTH):
    text(p, LEFT, y, line, "osl", SIZE, NAVY)
    y += LH
y += LH
bullet_w = FONTS_OBJ["osl"].text_length("• ", SIZE)
for item in FEATURES:
    lines = wrap(item, "osl", SIZE, WIDTH - bullet_w)
    text(p, LEFT, y, "• ", "osl", SIZE, RED)
    text(p, LEFT + bullet_w, y, lines[0], "osl", SIZE, NAVY)
    for extra in lines[1:]:
        y += LH
        text(p, LEFT, y, extra, "osl", SIZE, NAVY)
    y += LH
assert y < 400, "key features text overflows the page"

# 4.. - gallery
ref = fitz.open(REF)
for n, (tpl, mapping) in enumerate(GALLERY):
    p = doc[3 + n]
    # match copied images to template images by their placement on the page
    by_rect = {tuple(round(v) for v in ref[tpl].get_image_rects(x)[0]): pid
               for x, pid in mapping.items()}
    for (xref, *_rest) in p.get_images():
        key = tuple(round(v) for v in p.get_image_rects(xref)[0])
        replace(p, doc, xref, by_rect[key])


# last - contact page
CONTACT = {
    "name": "MARIE-EMMA MACHADO",
    "role": "Long term and sales director Brazil",
    "email": "marie@latinexclusive.com",
    "country": "BRA ",
    "phone": "+55 21 98393-0391",
    "photo": "assets/marie-emma.png",
    "address": ["Av. Atl\u00e2ntica, 4240 - Lj G",
                "Copacabana, Rio de Janeiro - RJ", "22070-002"],
}
p = doc[-1]
erase_text(p, [(30, 187, 215, 215), (353, 137, 600, 149), (353, 196, 600, 208),
               (353, 254, 600, 279)])
add_fonts(p)
RIGHT = 210.0
for s_, f_, sz, c_, y_ in [(CONTACT["name"], "osb", 12.27, WHITE, 198.6),
                           (CONTACT["role"], "osl", 10.23, GREY, 213.0)]:
    text(p, RIGHT - FONTS_OBJ[f_].text_length(s_, sz), y_, s_, f_, sz, c_)
# portrait replaces the logo inside the round badge (centre 280.5,202.5 r 53.5)
p.insert_image(fitz.Rect(226.5, 148.5, 334.5, 256.5), filename=CONTACT["photo"])
text(p, 355.0, 147.0, CONTACT["email"], "osl", 10.23, NAVY)
x = text(p, 355.0, 206.1, CONTACT["country"], "oss", 10.23, NAVY)
text(p, x, 206.1, CONTACT["phone"], "osl", 10.23, NAVY)
for i, line in enumerate(CONTACT["address"]):
    text(p, 355.0, 264.0 + 12 * i, line, "osl", 10.23, NAVY)

doc.subset_fonts()
doc.set_metadata({"title": f"{CODE} - {TITLE}", "creator": "Latin Exclusive"})
doc.save(OUT, garbage=4, deflate=True)
print("saved", OUT, len(doc), "pages")
