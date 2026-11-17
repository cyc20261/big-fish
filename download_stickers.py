"""Download whale-girl meme stickers from EDMOK/blue-fish-archive, crop to squares."""
import json, subprocess, os, sys

OUT_DIR = os.path.join(os.path.dirname(__file__), 'img', 'stickers')
os.makedirs(OUT_DIR, exist_ok=True)

# Get file list from GitHub API
result = subprocess.run(
    ['gh', 'api', 'repos/EDMOK/blue-fish-archive/contents/media'],
    capture_output=True, text=True, timeout=60
)
if result.returncode != 0:
    print(f'API ERROR: {result.stderr}')
    sys.exit(1)

data = json.loads(result.stdout)

# Filter for small images
candidates = []
for item in data:
    name = item['name'].lower()
    sz = item['size']
    if 5000 < sz < 500000:
        ext = os.path.splitext(name)[1]
        if ext in ('.png', '.jpg', '.jpeg', '.webp'):
            candidates.append(item)

print(f'Found {len(candidates)} candidates, downloading {min(40, len(candidates))}...')

downloaded = 0
for item in candidates[:40]:
    fname = item['name']
    out_path = os.path.join(OUT_DIR, fname)
    
    if os.path.exists(out_path):
        print(f'  SKIP {fname} (exists)')
        downloaded += 1
        continue
    
    print(f'  GET {fname} ({item["size"]:,}B)...', end=' ', flush=True)
    # Use stdout redirection instead of --output
    with open(out_path, 'wb') as f:
        r = subprocess.run(
            ['gh', 'api', f'repos/EDMOK/blue-fish-archive/contents/media/{fname}',
             '-H', 'Accept: application/vnd.github.raw'],
            stdout=f, stderr=subprocess.PIPE, timeout=120
        )
    if r.returncode == 0 and os.path.exists(out_path) and os.path.getsize(out_path) > 100:
        print(f'OK ({os.path.getsize(out_path):,}B)')
        downloaded += 1
    else:
        print(f'FAIL')
        if os.path.exists(out_path): os.remove(out_path)

print(f'\nDownloaded {downloaded} files. Cropping to squares...')

# Crop all downloaded images to center square
from PIL import Image
for fname in os.listdir(OUT_DIR):
    fpath = os.path.join(OUT_DIR, fname)
    if os.path.getsize(fpath) < 1000:
        continue
    try:
        img = Image.open(fpath).convert('RGBA')
        w, h = img.size
        s = min(w, h)
        left = (w - s) // 2
        top = (h - s) // 2
        cropped = img.crop((left, top, left + s, top + s))
        cropped = cropped.resize((400, 400), Image.LANCZOS)
        out = os.path.splitext(fpath)[0] + '.jpg'
        if cropped.mode == 'RGBA':
            bg = Image.new('RGB', cropped.size, (255, 255, 255))
            bg.paste(cropped, mask=cropped.split()[3])
            cropped = bg
        cropped.save(out, 'JPEG', quality=82)
        if out != fpath:
            os.remove(fpath)
        print(f'  OK {os.path.basename(out)}')
    except Exception as e:
        print(f'  ERR {fname}: {e}')

print('DONE!')