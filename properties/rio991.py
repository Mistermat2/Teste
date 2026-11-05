# Rio991 - Ipanema (photos: partner set, ids 01-22 from the site gallery)
CODE = "Rio991"
TITLE = "Renovated apartment in Ipanema"
DISTRICT = "Ipanema"
BEDROOMS, BATHROOMS, AREA = "3", "2", "200"
# shown under the district on the main-photo slide: (label, value) pairs
TERMS = [("Available from", "December 26"),
         ("Monthly rent", "approx. R$ 40,000")]
TERMS_NOTE = "Electricity not included"

DESCRIPTION = (
    "Located on Rua Visconde de Piraj\u00e1, facing Pra\u00e7a Nossa Senhora da Paz in "
    "Ipanema, this fully renovated 200 m\u00b2 apartment has a bright living room "
    "with mountain views, an integrated kitchen and three bedrooms. The building "
    "is 70 m from the metro, 280 m from the beach and 450 m from the Lagoa."
)
FEATURES = [
    "Fully renovated apartment",
    "Living room with integrated kitchen",
    "3 bedrooms, including 1 suite",
    "2 bathrooms, plus a powder room",
    "Split air conditioning in all rooms",
    "Automated curtains in the living room",
    "Custom-built wardrobes and cabinetry",
    "Virtual concierge and automated security system",
    "Part-time doorman",
    "1 covered parking space",
    "Available from December 26",
]

COVER_PHOTO = "01"      # cover + main photo (same image object in the template)
FEATURE_PHOTO = "03"
# (template page index, {template image xref: photo id})
GALLERY = [
    (5, {45: "04", 46: "05", 47: "06", 48: "07"}),
    (4, {38: "09", 39: "08", 40: "10"}),
    (6, {53: "11", 54: "12", 55: "13", 56: "14"}),
    (5, {45: "15", 46: "16", 47: "17", 48: "18"}),
    (6, {53: "19", 54: "20", 55: "21", 56: "22"}),
]
# horizontal focus (0=left, 0.5=centre, 1=right) when cropping to portrait
FOCUS = {"09": 0.3}
