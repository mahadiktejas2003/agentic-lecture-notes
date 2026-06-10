#!/usr/bin/env python3
"""
Auto-crop all frames in screenshots/ directory.
Removes black bars, uniform borders, and irrelevant desktop area
by detecting the content bounding box.
"""
import os
import sys
import logging
import statistics

try:
    from PIL import Image, ImageChops
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# Configure logging to write to both pipeline.log and stderr
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(sys.stderr)
    ]
)

def crop_content(img_path, padding=5):
    """Crop an image to its content bounding box with optional padding."""
    try:
        im = Image.open(img_path).convert('RGB')
    except Exception as e:
        logging.error(f"Failed to open image {img_path}: {e}")
        return False

    # 1. First attempt: Sample the corner pixel as background color
    corner_color = im.getpixel((0, 0))
    bg = Image.new('RGB', im.size, corner_color)
    diff = ImageChops.difference(im, bg)
    grey = diff.convert('L')
    bbox = grey.point(lambda x: 0 if x < 15 else 255).getbbox()
    
    use_fallback = False
    if bbox:
        x0, y0, x1, y1 = bbox
        crop_area = (x1 - x0) * (y1 - y0)
        orig_area = im.width * im.height
        # If crop area is < 20% of original frame (indicating aggressive crop), trigger fallback
        if crop_area < 0.2 * orig_area:
            logging.info(f"Corner crop yielded too small area ({crop_area}/{orig_area} = {crop_area/orig_area:.1%}). Using median border color fallback.")
            use_fallback = True
    else:
        logging.info(f"Corner crop yielded no bounding box. Using median border color fallback.")
        use_fallback = True

    # 2. Second attempt: Calculate median color of border pixels to determine crop bounds
    if use_fallback:
        border_pixels = []
        # Extract top and bottom rows
        for x in range(im.width):
            border_pixels.append(im.getpixel((x, 0)))
            border_pixels.append(im.getpixel((x, im.height - 1)))
        # Extract left and right columns (excluding corners)
        for y in range(1, im.height - 1):
            border_pixels.append(im.getpixel((0, y)))
            border_pixels.append(im.getpixel((im.width - 1, y)))
            
        r_median = int(statistics.median([p[0] for p in border_pixels]))
        g_median = int(statistics.median([p[1] for p in border_pixels]))
        b_median = int(statistics.median([p[2] for p in border_pixels]))
        median_color = (r_median, g_median, b_median)
        
        bg = Image.new('RGB', im.size, median_color)
        diff = ImageChops.difference(im, bg)
        grey = diff.convert('L')
        bbox = grey.point(lambda x: 0 if x < 15 else 255).getbbox()

    if bbox:
        # Add padding while staying within image bounds
        x0 = max(0, bbox[0] - padding)
        y0 = max(0, bbox[1] - padding)
        x1 = min(im.width, bbox[2] + padding)
        y1 = min(im.height, bbox[3] + padding)
        
        # Verify the final cropped area makes sense
        final_area = (x1 - x0) * (y1 - y0)
        orig_area = im.width * im.height
        if final_area < 0.05 * orig_area:
            logging.warning(f"Final crop area for {os.path.basename(img_path)} is extremely small ({final_area/orig_area:.1%}). Skipping crop to prevent empty image.")
            return False
            
        try:
            cropped = im.crop((x0, y0, x1, y1))
            cropped.save(img_path)
            return True
        except Exception as e:
            logging.error(f"Failed to save cropped image: {e}")
            return False
            
    return False

def main():
    screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')
    if not os.path.isdir(screenshots_dir):
        logging.info(f"No screenshots/ directory found at {screenshots_dir}. Nothing to crop.")
        return

    files = sorted(f for f in os.listdir(screenshots_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png')))
    if not files:
        logging.info("No image files found in screenshots/.")
        return

    logging.info(f"Cropping {len(files)} frame(s) in {screenshots_dir}...")
    for fname in files:
        path = os.path.join(screenshots_dir, fname)
        if crop_content(path):
            logging.info(f"  ✓ Cropped: {fname}")
        else:
            logging.info(f"  – Skipped (no distinct content bbox or crop unsafe): {fname}")

    logging.info("Done.")

if __name__ == '__main__':
    main()
