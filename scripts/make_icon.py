from PIL import Image
import os

def create_ico():
    source_path = "static/staticimg/LightBlastblack.png"
    dest_path = "app.ico"
    
    if not os.path.exists(source_path):
        print(f"Error: {source_path} not found!")
        return

    try:
        img = Image.open(source_path)
        # ICOs often contain multiple sizes
        icon_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        img.save(dest_path, format='ICO', sizes=icon_sizes)
        print(f"Success! Created {dest_path}")
    except Exception as e:
        print(f"Failed to create icon: {e}")

if __name__ == "__main__":
    create_ico()
