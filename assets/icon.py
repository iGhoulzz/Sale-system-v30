"""
Generate a simple application icon for the Sales Management System
and save it to assets/icon.png
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create a 256x256 icon
    img_size = 256
    icon = Image.new('RGBA', (img_size, img_size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # Background circle
    circle_margin = 10
    circle_diameter = img_size - (circle_margin * 2)
    circle_position = (circle_margin, circle_margin, img_size - circle_margin, img_size - circle_margin)
    
    # Draw blue circle background
    draw.ellipse(circle_position, fill="#3454D1")
    
    # Draw letter "S" in white
    try:
        # Try to load a font - Arial on Windows, DejaVuSans on Linux
        font_name = "Arial.ttf" if os.name == 'nt' else "DejaVuSans.ttf"
        try:
            font = ImageFont.truetype(font_name, 150)
        except IOError:
            # Fallback to default font
            font = ImageFont.load_default()
            
        # Position the text in the center - using updated method
        text = "S"
        left, top, right, bottom = font.getbbox(text)
        w, h = right - left, bottom - top
        position = ((img_size - w) // 2 - left, (img_size - h) // 2 - top - 15)  # Slight adjustment
        
        # Draw shadow
        shadow_pos = (position[0] + 5, position[1] + 5)
        draw.text(shadow_pos, text, fill=(0, 0, 0, 100), font=font)
        
        # Draw text
        draw.text(position, text, fill="white", font=font)
    except Exception as e:
        # Fallback if font operations fail
        print(f"Error with font: {e}")
        # Draw a simple rectangle
        margin = 60
        draw.rectangle([margin, margin, img_size - margin, img_size - margin], 
                      fill="#FFFFFF", outline="#FFFFFF", width=5)
        
    # Save the icon
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    icon.save(icon_path)
    print(f"Icon saved to {icon_path}")
    return icon_path

if __name__ == "__main__":
    create_icon() 