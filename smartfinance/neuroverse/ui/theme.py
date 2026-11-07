"""NatWest-inspired palette: deep purple, bright magenta accent, teal and mint.

Original colours chosen to feel like the sponsor's brand. No NatWest logos or marks are used.
Text colours are picked to keep good contrast on their backgrounds.
"""

TEXT_SCALE = 1.0          # app.py sets this to 1.25 when "larger text" is switched on

# surfaces
BG = '#f4f1f8'
SURFACE = '#ffffff'
BORDER = '#ddd3e8'

# brand
PRIMARY = '#5a287d'
PRIMARY_DARK = '#42145f'
PRIMARY_LIGHT = '#ebe3f3'
PRIMARY_HOVER = '#42145f'
PINK = '#e5007d'          # accent (shapes, focus rings), not for small text
TEAL = '#007c78'
MINT = '#4fd1b8'
YELLOW = '#ffc845'
BLUE = '#3d8bfd'

# text
TEXT = '#24103a'
MUTED = '#5d5670'
DANGER = '#b3123b'
GOOD = '#00775f'
INK = '#24103a'

# sidebar
NAV = '#42145f'
NAV_SELECTED = '#ffffff'
NAV_HOVER = '#5a287d'
NAV_TEXT = '#efe6f7'
NAV_MUTED = '#cdbbe0'

# hero banner
HERO_TOP = '#5a287d'
HERO_BOTTOM = '#42145f'
HERO_END = '#b3127f'

# keyboard focus rings
FOCUS = '#e5007d'
FOCUS_ON_DARK = '#ffc845'

FONT = 'Arial'


def font(size, weight='normal'):
    """Font tuple scaled by the larger-text preference. Use for text drawn on canvases."""
    return (FONT, max(7, round(size * TEXT_SCALE)), weight)

