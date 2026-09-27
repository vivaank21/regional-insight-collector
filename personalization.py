"""
personalization.py
--------------------
Decides which regional image and short tagline to show a visitor based
on their approximate geolocation.
"""

# Maps a normalized state/region name to (folder-name, display tagline).
_INDIA_REGIONS = {
    "gujarat": ("gujarat", "The land of the Rann and relentless enterprise."),
    "maharashtra": ("maharashtra", "Where the Western Ghats meet the sea."),
    "rajasthan": ("rajasthan", "Desert forts and centuries of color."),
    "delhi": ("delhi", "Where ancient capitals still stand."),
    "nct of delhi": ("delhi", "Where ancient capitals still stand."),
}

_FALLBACKS = {
    "india": ("india", "A glimpse of the Indian subcontinent."),
    "international": ("default", "A glimpse of your part of the world."),
    "unknown": ("default", "Your region is a mystery to us right now."),
}

# Relative path (inside static/) to a single representative image for
# each folder. The project ships lightweight placeholder SVGs; replace
# these with real photography whenever you like.
_IMAGE_FILENAME = "region.svg"


def get_regional_image(country, region, state, city):
    """
    Return a dict describing the personalization content for a visitor:
        {
            "folder": "gujarat" | "maharashtra" | ... | "india" | "default",
            "image_path": "images/<folder>/region.svg",
            "tagline": "<short regional tagline>",
        }

    Falls back gracefully through: named Indian state -> India generic ->
    international generic -> unknown/default.
    """
    country_norm = (country or "").strip().lower()
    state_norm = (state or "").strip().lower()
    region_norm = (region or "").strip().lower()

    if country_norm in ("unknown", ""):
        folder, tagline = _FALLBACKS["unknown"]
        return _build_result(folder, tagline)

    if country_norm == "india":
        for key in (state_norm, region_norm):
            if key in _INDIA_REGIONS:
                folder, tagline = _INDIA_REGIONS[key]
                return _build_result(folder, tagline)
        folder, tagline = _FALLBACKS["india"]
        return _build_result(folder, tagline)

    folder, tagline = _FALLBACKS["international"]
    return _build_result(folder, tagline)


def _build_result(folder, tagline):
    return {
        "folder": folder,
        "image_path": f"images/{folder}/{_IMAGE_FILENAME}",
        "tagline": tagline,
    }
