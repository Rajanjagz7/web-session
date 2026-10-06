"""Generate 100 illustrated avatar PNGs (gradient background, shoulders, head, hair) - deterministic, no external fetches."""
import os, random
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed-images")
os.makedirs(OUT, exist_ok=True)
S = 512
PAL = [((98, 182, 245), (245, 143, 124)), ((132, 214, 190), (245, 190, 120)), ((160, 140, 240), (250, 160, 190)), ((110, 200, 230), (190, 160, 245)),
       ((250, 190, 130), (240, 130, 150)), ((120, 210, 160), (100, 170, 235))]
SKIN = [(255, 224, 200), (245, 200, 165), (222, 170, 130), (190, 135, 100), (150, 105, 80)]
HAIR = [(40, 28, 70), (60, 40, 30), (25, 25, 30), (150, 90, 45), (200, 150, 70), (110, 60, 40), (230, 200, 130)]
SHIRT = [(245, 125, 105), (90, 90, 230), (40, 180, 160), (250, 190, 90), (150, 130, 230), (80, 160, 220)]

for i in range(100):
    r = random.Random(1000 + i)
    a, b = PAL[i % len(PAL)]
    img = Image.new("RGB", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * S)
            px[x, y] = tuple(int(a[k] * (1 - t) + b[k] * t) for k in range(3))
    d = ImageDraw.Draw(img)
    skin, hair, shirt = r.choice(SKIN), r.choice(HAIR), r.choice(SHIRT)
    d.ellipse([90, 360, 422, 760], fill=shirt)
    d.rectangle([226, 300, 286, 390], fill=tuple(int(c * 0.93) for c in skin))
    if r.random() < 0.55:
        d.rounded_rectangle([150, 130, 362, 400], radius=90, fill=hair)
    d.ellipse([176, 150, 336, 330], fill=skin)
    d.pieslice([166, 128, 346, 280], 180, 360, fill=hair)
    for ex in (222, 290):
        d.ellipse([ex - 7, 232, ex + 7, 246], fill=(40, 30, 50))
    d.arc([226, 258, 286, 300], 20, 160, fill=(150, 70, 70), width=5)
    d.ellipse([196, 262, 224, 282], fill=(255, 150, 140))
    d.ellipse([288, 262, 316, 282], fill=(255, 150, 140))
    img.save(os.path.join(OUT, f"avatar-{i + 1:03d}.png"))
print(len(os.listdir(OUT)), "avatars in", OUT)
