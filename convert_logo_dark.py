from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors

# Load the SVG
drawing = svg2rlg("logo.svg")

# Create a new drawing with the same dimensions
width = drawing.width
height = drawing.height
new_drawing = Drawing(width, height)

# Add a black background rectangle
# x, y, width, height
bg = Rect(0, 0, width, height)
bg.fillColor = colors.black
bg.strokeColor = None
new_drawing.add(bg)

# Add the original SVG content on top
new_drawing.add(drawing)

# Save as PNG
renderPM.drawToFile(new_drawing, "logo_dark.png", fmt="PNG")
print("✅ Generated logo_dark.png with black background.")
