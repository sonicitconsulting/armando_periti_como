from PIL import Image
from io import BytesIO
import base64

def load_image(image_path):
    with Image.open(image_path) as img:
        buf = BytesIO()
        img.save(buf, format="PNG")  # puoi forzare PNG anche se il file è jpg
        b64 = base64.b64encode(buf.getvalue()).decode()
        data_url = f"data:image/png;base64,{b64}"

    return data_url