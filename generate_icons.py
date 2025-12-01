
import os
from PIL import Image

def generate_icons(source_path, output_dir):
    if not os.path.exists(source_path):
        print(f"Error: Source image not found at {source_path}")
        return

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        img = Image.open(source_path)
        sizes = [16, 32, 48, 128]
        
        for size in sizes:
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            output_path = os.path.join(output_dir, f"icon{size}.png")
            resized_img.save(output_path)
            print(f"Generated {output_path}")
            
        print("All icons generated successfully!")
    except Exception as e:
        print(f"Error generating icons: {e}")

if __name__ == "__main__":
    # Use the uploaded image path
    source = "C:/Users/jaisu/.gemini/antigravity/brain/a0ee4739-a9f2-4b9e-be16-134a267aba24/uploaded_image_1764329327184.png"
    output = "extension/icons"
    generate_icons(source, output)
