#!/usr/bin/env python3
"""
Auto-Generate Descriptive Titles for Gallery Images
Uses Ollama + LLaVA to analyze images and generate meaningful descriptions.

Usage:
    python generate_descriptions.py

Features:
    - Auto-save progress (resume if interrupted)
    - Progress bar
    - Error recovery
    - Parallel processing (multiple images at once)
    - Generates ready-to-use JavaScript output
"""

import os
import re
import json
import base64
import requests
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
except ImportError:
    print("Installing tqdm...")
    os.system("pip install tqdm")
    from tqdm import tqdm

# ============================================================================
# CONFIGURATION - Ubah di sini jika perlu
# ============================================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llava:34b"  # Model yang lebih berkualiti
MAX_WORKERS = 3      # Bilangan gambar diprocess serentak (2-4 recommended)

BASE_DIR = Path(__file__).parent.parent  # D:\Projects\portfolio-website\samples\faiz
DESIGN_HTML = BASE_DIR / "design.html"

# Fail output berbeza untuk model 34b (supaya boleh compare dengan 13b)
PROGRESS_FILE = BASE_DIR / "progress_34b.json"
OUTPUT_FILE = BASE_DIR / "gallery_data_34b.js"
ERROR_LOG = BASE_DIR / "error_log_34b.txt"

# ============================================================================

# Thread lock untuk safe file writing
progress_lock = threading.Lock()

# Prompt for image description
PROMPT = """Look at this image and provide a short, descriptive title (5-15 words) that describes what the image shows.

Rules:
- Be specific about the content (e.g., "Gaming Tournament Poster for Menjerit Event" not just "Poster")
- If there's text in the image, include key words from it
- If it's a logo, describe whose logo and style
- If it's a jersey design, mention team/style/colors
- Keep it concise but descriptive
- DO NOT start with "This is" or "A"
- Just give me the title, nothing else

Title:"""


def load_progress():
    """Load progress from checkpoint file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": {}, "errors": [], "last_updated": None, "model": MODEL}


def save_progress(progress):
    """Save progress to checkpoint file (thread-safe)."""
    with progress_lock:
        progress["last_updated"] = datetime.now().isoformat()
        progress["model"] = MODEL
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)


def log_error(message):
    """Log error to file (thread-safe)."""
    with progress_lock:
        with open(ERROR_LOG, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")


def extract_gallery_data(html_path):
    """Extract galleryData from design.html."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the galleryData object
    pattern = r'const\s+galleryData\s*=\s*\{([\s\S]*?)\};'
    match = re.search(pattern, content)

    if not match:
        raise ValueError("Could not find galleryData in design.html")

    gallery_text = match.group(1)

    # Parse each category
    categories = {}
    category_pattern = r"(\w+):\s*\[([\s\S]*?)\]"

    for cat_match in re.finditer(category_pattern, gallery_text):
        category_name = cat_match.group(1)
        items_text = cat_match.group(2)

        # Parse individual items
        items = []
        item_pattern = r"\{\s*src:\s*['\"]([^'\"]+)['\"],\s*title:\s*['\"]([^'\"]*)['\"]"

        for item_match in re.finditer(item_pattern, items_text):
            items.append({
                "src": item_match.group(1),
                "title": item_match.group(2)
            })

        categories[category_name] = items

    return categories


def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def get_image_description(image_path):
    """Get description from Ollama LLaVA."""
    try:
        image_base64 = encode_image(image_path)

        payload = {
            "model": MODEL,
            "prompt": PROMPT,
            "images": [image_base64],
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=600)  # 10 min timeout untuk 34b
        response.raise_for_status()

        result = response.json()
        description = result.get("response", "").strip()

        # Clean up the description
        description = description.replace('"', '').replace("'", "")
        description = re.sub(r'^(Title:|title:)\s*', '', description)
        description = description.strip()

        # Remove leading "A " or "An " if present
        description = re.sub(r'^(A |An )', '', description)

        # Limit length
        if len(description) > 100:
            description = description[:97] + "..."

        return description if description else None

    except requests.exceptions.Timeout:
        log_error(f"Timeout processing: {image_path}")
        return None
    except Exception as e:
        log_error(f"Error processing {image_path}: {str(e)}")
        return None


def process_single_image(img_data, progress):
    """Process a single image and return result."""
    src = img_data["src"]
    image_path = BASE_DIR / src

    if not image_path.exists():
        log_error(f"File not found: {image_path}")
        return {"src": src, "description": None, "error": True}

    description = get_image_description(image_path)

    if description:
        return {"src": src, "description": description, "error": False}
    else:
        return {"src": src, "description": img_data["original_title"], "error": True}


def generate_output(categories, progress):
    """Generate JavaScript output file."""
    output_lines = ["const galleryData = {"]

    for category_name, items in categories.items():
        output_lines.append(f"    {category_name}: [")

        for item in items:
            src = item["src"]
            # Use new title if available, otherwise keep original
            title = progress["completed"].get(src, item["title"])
            # Escape single quotes in title
            title = title.replace("'", "\\'")
            output_lines.append(f"        {{ src: '{src}', title: '{title}' }},")

        output_lines.append("    ],")

    output_lines.append("};")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))


def main():
    print("=" * 60)
    print("Gallery Image Description Generator")
    print(f"Using Ollama + {MODEL}")
    print(f"Parallel Workers: {MAX_WORKERS}")
    print("=" * 60)

    # Check Ollama is running
    try:
        requests.get("http://localhost:11434/api/tags", timeout=5)
        print("[OK] Ollama is running")
    except:
        print("[ERROR] Ollama is not running!")
        print("Please start Ollama with: ollama serve")
        return

    # Check model is available
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in response.json().get("models", [])]
        model_base = MODEL.split(":")[0]
        if not any(model_base in m for m in models):
            print(f"[ERROR] Model {MODEL} not found!")
            print(f"Available models: {models}")
            print(f"Please run: ollama pull {MODEL}")
            return
        print(f"[OK] Model {MODEL} is available")
    except Exception as e:
        print(f"[WARNING] Could not verify model: {e}")

    # Load existing progress
    progress = load_progress()
    completed_count = len(progress["completed"])

    if completed_count > 0:
        print(f"[INFO] Resuming from checkpoint: {completed_count} images already processed")

    # Extract gallery data
    print(f"[INFO] Parsing {DESIGN_HTML}...")
    try:
        categories = extract_gallery_data(DESIGN_HTML)
    except Exception as e:
        print(f"[ERROR] Failed to parse design.html: {e}")
        return

    # Count total images
    total_images = sum(len(items) for items in categories.values())
    print(f"[INFO] Found {total_images} images in {len(categories)} categories")

    # Collect all images to process
    all_images = []
    for category_name, items in categories.items():
        for item in items:
            all_images.append({
                "category": category_name,
                "src": item["src"],
                "original_title": item["title"]
            })

    # Filter out already completed
    to_process = [img for img in all_images if img["src"] not in progress["completed"]]

    if not to_process:
        print("[INFO] All images already processed!")
        generate_output(categories, progress)
        print(f"[DONE] Output saved to: {OUTPUT_FILE}")
        return

    print(f"[INFO] Processing {len(to_process)} remaining images...")
    print(f"[INFO] Using {MAX_WORKERS} parallel workers")
    print("-" * 60)

    # Process images with parallel workers
    processed_count = 0
    error_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_img = {
            executor.submit(process_single_image, img, progress): img
            for img in to_process
        }

        # Process results as they complete
        with tqdm(total=len(to_process), desc="Processing", unit="img") as pbar:
            for future in as_completed(future_to_img):
                result = future.result()
                src = result["src"]

                if result["description"]:
                    progress["completed"][src] = result["description"]
                    processed_count += 1

                if result["error"]:
                    if src not in progress["errors"]:
                        progress["errors"].append(src)
                    error_count += 1

                # Auto-save after each image
                save_progress(progress)

                # Generate output periodically (every 10 images)
                if len(progress["completed"]) % 10 == 0:
                    with progress_lock:
                        generate_output(categories, progress)

                pbar.update(1)

    # Final output
    generate_output(categories, progress)

    print("-" * 60)
    print(f"[DONE] Processed {len(progress['completed'])} images")
    print(f"[DONE] Errors: {len(progress['errors'])}")
    print(f"[DONE] Output saved to: {OUTPUT_FILE}")
    print(f"[DONE] Progress saved to: {PROGRESS_FILE}")

    if progress["errors"]:
        print(f"[INFO] Check {ERROR_LOG} for error details")


if __name__ == "__main__":
    main()
