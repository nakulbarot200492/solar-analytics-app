from PIL import Image
import os

src = "/Users/macbook/.gemini/antigravity/brain/936d4a0d-21c1-4797-82c9-d8f98c024b5f/solar_app_icon_512_1779022019021.png"
base = "/Users/macbook/Documents/solar-analytics-app/android/app/src/main/res"

sizes = {
    "mipmap-ldpi":    36,
    "mipmap-mdpi":    48,
    "mipmap-hdpi":    72,
    "mipmap-xhdpi":   96,
    "mipmap-xxhdpi":  144,
    "mipmap-xxxhdpi": 192,
}

img = Image.open(src).convert("RGBA")

for folder, size in sizes.items():
    out_dir = os.path.join(base, folder)
    os.makedirs(out_dir, exist_ok=True)
    resized = img.resize((size, size), Image.LANCZOS)
    resized.save(os.path.join(out_dir, "ic_launcher.png"), "PNG")
    resized.save(os.path.join(out_dir, "ic_launcher_round.png"), "PNG")
    print(f"✅ {folder} ({size}x{size})")

play = img.resize((512, 512), Image.LANCZOS)
play.save("/Users/macbook/Documents/solar-analytics-app/assets/play_store_icon_512.png", "PNG")
print("✅ assets/play_store_icon_512.png (512x512) — use this for Play Store upload")
print("\nAll icons placed!")
