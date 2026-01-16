"""
Simple script to create a basic app icon.
This creates a minimal .ico file for the application.
"""
from PIL import Image, ImageDraw
import os

def create_app_icon():
    """Create a simple app icon."""
    # Create a 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple PDF document icon
    # Background circle
    margin = 20
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=(52, 152, 219), outline=(41, 128, 185), width=4)
    
    # PDF document shape
    doc_left = size // 2 - 60
    doc_top = size // 2 - 40
    doc_right = size // 2 + 60
    doc_bottom = size // 2 + 40
    
    draw.rectangle([doc_left, doc_top, doc_right, doc_bottom], 
                  fill='white', outline=(149, 165, 166), width=2)
    
    # PDF text
    draw.text((doc_left + 20, doc_top + 15), "PDF", 
             fill=(52, 152, 219), font_size=20)
    
    # Download arrow
    arrow_x = size // 2
    arrow_y = size // 2 + 60
    
    # Arrow shaft
    draw.rectangle([arrow_x - 2, arrow_y - 20, arrow_x + 2, arrow_y + 20], 
                  fill=(46, 204, 113))
    
    # Arrow head
    points = [
        (arrow_x, arrow_y + 25),
        (arrow_x - 8, arrow_y + 15),
        (arrow_x + 8, arrow_y + 15)
    ]
    draw.polygon(points, fill=(46, 204, 113))
    
    # Save as ICO file with multiple sizes
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Create list of images for ICO
    ico_images = []
    for ico_size in icon_sizes:
        resized = img.resize(ico_size, Image.Resampling.LANCZOS)
        ico_images.append(resized)
    
    # Save as ICO
    img.save('app_icon.ico', format='ICO', sizes=[(img.width, img.height) for img in ico_images])
    print(f"Created app_icon.ico with sizes: {icon_sizes}")
    
    return 'app_icon.ico'

if __name__ == "__main__":
    try:
        create_app_icon()
        print("✅ Icon created successfully!")
    except ImportError:
        print("❌ PIL not available. Creating simple placeholder...")
        # Create a simple text file as placeholder
        with open('app_icon.ico', 'w') as f:
            f.write("# Placeholder for app icon\n")
        print("⚠️ Created placeholder icon file")
