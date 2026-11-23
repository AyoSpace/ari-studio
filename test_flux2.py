"""Compare Cloudflare image models. Run:  python3 test_flux2.py
Optional reference photo (must be small):  python3 test_flux2.py --ref me.jpg
Saves one image per model and never prints secrets."""
import base64, json, os, sys, urllib.error, urllib.request, uuid

ACCOUNT = os.environ["CF_ACCOUNT_ID"].strip()
TOKEN = os.environ["CF_API_TOKEN"].strip()
MODELS = [
    "@cf/black-forest-labs/flux-1-schnell",
    "@cf/black-forest-labs/flux-2-klein-4b",
    "@cf/black-forest-labs/flux-2-klein-9b",
]
PROMPT = ("Full-length editorial fashion photograph of a model standing in a sunlit Lagos street, "
          "wearing black ankle-length trousers with a grey leather patch at each ankle and a plain white shirt, "
          "golden hour light, colourful buildings in the background, entire outfit visible from head to shoes")

ref = None
if "--ref" in sys.argv:
    path = sys.argv[sys.argv.index("--ref") + 1]
    try:
        from PIL import Image
        import io
        im = Image.open(path).convert("RGB")
        im.thumbnail((500, 500))           # references must be under 512x512
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=90); ref = buf.getvalue()
        PROMPT = ("The person in the reference image wearing black ankle-length trousers with a grey leather patch "
                  "at each ankle and a plain white shirt, standing in a sunlit Lagos street, golden hour, full body visible. "
                  "Keep the person's face, hair, skin tone and body proportions exactly as in the reference.")
    except ImportError:
        sys.exit("Install Pillow first:  pip install pillow")

def multipart(fields, files):
    b = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    for k, (name, data) in files.items():
        out += (f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{name}"\r\n'
                f'Content-Type: image/jpeg\r\n\r\n').encode() + data + b"\r\n"
    out += f"--{b}--\r\n".encode()
    return out, f"multipart/form-data; boundary={b}"

for model in MODELS:
    short = model.split("/")[-1]
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT}/ai/run/{model}"
    try:
        if "flux-1" in model:
            if ref: print(short, ": skipped (does not take reference images)"); continue
            body, ctype = json.dumps({"prompt": PROMPT}).encode(), "application/json"
        else:
            files = {"input_image_0": ("ref.jpg", ref)} if ref else {}
            body, ctype = multipart({"prompt": PROMPT, "width": "1024", "height": "1024"}, files)
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": "Bearer " + TOKEN, "Content-Type": ctype, "User-Agent": "ari-studio/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.load(r)
        img = (d.get("result") or {}).get("image")
        if not img: print(short, ": no image:", d.get("errors")); continue
        raw = base64.b64decode(img)
        fn = f"out-{short}{'-ref' if ref else ''}." + ("png" if raw[:4] == b"\x89PNG" else "jpg")
        open(fn, "wb").write(raw); print(short, ": saved", fn)
    except urllib.error.HTTPError as e:
        print(short, ": HTTP", e.code, e.read().decode()[:200])
    except Exception as e:
        print(short, ": failed", type(e).__name__)
