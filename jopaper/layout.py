from PIL import Image
from typing import Tuple, List
import io


class SubImage:
    def __init__(self, filename: str, width: int, height: int):
        self.filename = filename
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0

    def to_box(self, box_x: int, box_y: int, box_width: int, box_height: int):
        scale = min(self.width / box_width, self.height / box_height)
        self.width = int(self.width / scale)
        self.height = int(self.height / scale)
        self.box_width = box_width
        self.box_height = box_height
        self.x = box_x
        self.y = box_y

    def get_image(self):
        with Image.open(self.filename) as img:
            img = self._scale(img)
            img = self._crop(img)
        return img

    def get_pos(self):
        return self.x, self.y

    def get_ratio(self):
        return self.width / self.height

    def get_size(self):
        return self.width, self.height

    def _attr(self, key, defval):
        return getattr(self, key) if hasattr(self, key) else defval

    def _scale(self, img):
        return img.resize((self.width, self.height))

    def _crop(self, img):
        w = self.width
        h = self.height
        bw = self._attr("box_width", self.width)
        bh = self._attr("box_height", self.height)
        if w > bw or h > bh:
            nw = min(w, bw)
            nh = min(h, bh)
            nx = (w - nw) // 2
            ny = (h - nh) // 2
            img = img.crop((nx, ny, nx + nw, ny + nh))
            self.x += (bw - nw) // 2
            self.y += (bh - nh) // 2
        return img


class Wall:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.subs = []

    def add(self, subimage):
        self.subs.append(subimage)

    def get_png(self, tracer) -> Tuple[List[str], bytes]:
        with tracer.start_as_current_span("Image.new"):
            wall = Image.new("RGB", (self.width, self.height))
        with tracer.start_as_current_span("arrange_boxes"):
            arranged = self._arrange_used_boxes()
        assert arranged

        used_keys = []
        for sub in arranged:
            with tracer.start_as_current_span("get_image"):
                img = sub.get_image()
            with tracer.start_as_current_span("paste"):
                wall.paste(img, sub.get_pos())
            used_keys.append(sub.filename)
        buff = io.BytesIO()
        with tracer.start_as_current_span("wall.save"):
            wall.save(buff, format="PNG")
        return used_keys, buff.getvalue()

    def _arrange_used_boxes(self):
        assert self.subs
        arranged = layout_r_c(1, len(self.subs), self.width, self.height, self.subs)
        return arranged


# r rows, c cols
def layout_r_c(r, c, screen_w, screen_h, boxes):
    """
    Lay out into @r rows and @c columns
    Cell sizes are proportional to image sizes
    """
    if len(boxes) != r * c:
        return None

    row_h = [0] * r
    col_w = [0] * c
    row_th = 0
    col_tw = 0
    for rn in range(r):
        for cn in range(c):
            w, h = boxes[rn * c + cn].get_size()
            col_w[cn] += w
            row_h[rn] += h
            col_tw += w
            row_th += h
    row_h = [screen_h * h // row_th for h in row_h]
    col_w = [screen_w * w // col_tw for w in col_w]

    ret = []
    ry = 0
    for rn in range(r):
        cx = 0
        rh = row_h[rn]
        for cn in range(c):
            cw = col_w[cn]
            b = boxes[rn * c + cn]
            w, h = b.get_size()
            b.to_box(cx, ry, cw, rh)
            ret.append(b)
            cx += col_w[cn]
        ry += row_h[rn]
    return ret
