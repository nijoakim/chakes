import random

_ADJECTIVES = [
    "amber", "azure", "cobalt", "coral", "crimson", "cyan", "dusk", "ember",
    "fern", "frost", "gilded", "indigo", "jade", "lunar", "maroon", "midnight",
    "nebula", "obsidian", "onyx", "opal", "pearl", "prism", "quartz", "rose",
    "ruby", "sable", "scarlet", "silver", "solar", "teal", "topaz", "violet",
]

_NOUNS = [
    "andromeda", "aurora", "ceres", "comet", "cosmos", "eclipse", "equinox",
    "galaxy", "helion", "horizon", "io", "kepler", "lyra", "meteor", "nebula",
    "nexus", "nova", "orion", "parallax", "pegasus", "perihelion", "pleiades",
    "pulsar", "quasar", "rigel", "sirius", "solstice", "titan", "vega", "zenith",
    "zephyr", "zodiac",
]


def generate_server_name() -> str:
    return f"{random.choice(_ADJECTIVES)}-{random.choice(_NOUNS)}"


SERVER_NAME: str = generate_server_name()
