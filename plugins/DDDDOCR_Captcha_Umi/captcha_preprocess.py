import io


def open_image(image_bytes):
    from PIL import Image

    image = Image.open(io.BytesIO(image_bytes))
    image.load()
    return image.convert("RGB")


def image_size(image_bytes):
    image = open_image(image_bytes)
    return image.size


def conservative_gray_removal(image_bytes, max_chroma=8, min_luma=105, max_luma=242):
    """Whiten only nearly neutral mid-tone pixels; always used alongside raw."""
    import numpy as np

    image = open_image(image_bytes)
    array = np.asarray(image, dtype=np.uint8).copy()
    high = array.max(axis=2).astype(np.int16)
    low = array.min(axis=2).astype(np.int16)
    chroma = high - low
    luma = (
        array[:, :, 0].astype(np.float32) * 0.299
        + array[:, :, 1].astype(np.float32) * 0.587
        + array[:, :, 2].astype(np.float32) * 0.114
    )
    mask = (chroma <= int(max_chroma)) & (luma >= int(min_luma)) & (luma <= int(max_luma))
    array[mask] = 255
    out = io.BytesIO()
    from PIL import Image

    Image.fromarray(array, "RGB").save(out, format="PNG")
    return out.getvalue(), int(mask.sum())
