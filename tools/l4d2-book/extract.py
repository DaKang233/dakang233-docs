"""Read tagged InDesign PDFs into an ordered representation for the web edition."""
import argparse
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import fitz
import pdfplumber
from PIL import Image


KID = re.compile(r"<<.*?>>|(\d+)\s+\d+\s+R|(\d+)", re.S)
LIGATURES = str.maketrans({"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"})


def clean(text):
    return unicodedata.normalize("NFC", text.translate(LIGATURES)).replace("\u00ad", "").replace("\u200b", "")


def bbox(objects):
    return [min(o["x0"] for o in objects), min(o["top"] for o in objects),
            max(o["x1"] for o in objects), max(o["bottom"] for o in objects)]


def first_number(value):
    return int(value.split()[0])


class Extraction:
    def __init__(self, source, asset_dir):
        self.doc = fitz.open(source)
        self.source = source
        self.asset_dir = asset_dir
        self.page_numbers = {p.xref: p.number + 1 for p in self.doc}
        self.marked = {}
        self.used = set()
        self.asset_dir.mkdir(parents=True, exist_ok=True)
        self.destinations = self.doc.resolve_names()

    def read_marks(self):
        with pdfplumber.open(self.source, unicode_norm="NFC") as pdf:
            for i, page in enumerate(pdf.pages, 1):
                groups = defaultdict(list)
                images = defaultdict(list)
                for char in page.chars:
                    if char.get("mcid") is not None:
                        groups[char["mcid"]].append(char)
                for im in page.images:
                    if im.get("mcid") is not None:
                        images[im["mcid"]].append(im)
                for mark in groups.keys() | images.keys():
                    chars = groups[mark]
                    if chars:
                        raw = "".join(o["text"] for o in chars)
                        # Embedded PDF codepoints include custom bullet and footnote fonts.
                        font = chars[0]["fontname"].split("+")[-1]
                        content = clean(raw)
                        if "RopeSequenceNumber" in font and re.fullmatch(r"\s*[a-z]\s*", content):
                            font = "footnote-marker"
                        # Keep the baseline and horizontal origin for line reflow.
                        visual = bbox(chars)
                        base = chars[0]["y0"] + chars[0]["size"] * 0.18
                    else:
                        content, font, visual, base = "", "", None, None
                    self.marked[i, mark] = {
                        "page": i, "mark": mark, "text": content, "font": font, "box": visual,
                        "base": round(base, 1) if base is not None else None,
                        "image_boxes": [bbox([o]) for o in images[mark]],
                    }
                page.close()

    def named_page(self, name):
        if not name:
            return None
        result = self.destinations.get(name)
        if result is None:
            try:
                result = self.destinations.get(name.encode("latin1").decode("utf8"))
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        return result["page"] + 1 if result and result.get("page", -1) >= 0 else None

    def image(self, page, box):
        p = self.doc[page - 1]
        rect = fitz.Rect(box) & p.rect
        if rect.is_empty or rect.width < 3 or rect.height < 3:
            return None
        scale = min(2.4, 1440 / max(rect.width, rect.height))
        pix = p.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect, alpha=False)
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        asset = hashlib.sha256(im.tobytes() + str(im.size).encode()).hexdigest()[:20] + ".webp"
        dest = self.asset_dir / asset
        if not dest.exists():
            im.save(dest, quality=91, method=4)
        return {"asset": asset, "width": pix.width, "height": pix.height, "display": round(rect.width)}

    def visit(self, xref, page=None):
        doc = self.doc
        role = doc.xref_get_key(xref, "S")[1].removeprefix("/")
        if role in {"TOC", "TOCI"}:
            return None
        pg = doc.xref_get_key(xref, "Pg")
        if pg[0] == "xref":
            page = self.page_numbers.get(first_number(pg[1]), page)
        typ, value = doc.xref_get_key(xref, "K")
        if typ == "null" and role not in {"TD", "TH"}:
            return None
        if typ == "xref" and doc.xref_get_key(first_number(value), "S")[0] == "null":
            value = doc.xref_object(first_number(value), compressed=True)

        def mark_on(p, mcid):
            key = p, int(mcid)
            self.used.add(key)
            return self.marked.get(key)

        children = []
        annotations = []
        for part in KID.finditer(value):
            if part[1]:
                child = self.visit(int(part[1]), page)
            elif part[2]:
                child = mark_on(page, part[2])
            else:
                pg_match = re.search(r"/Pg\s+(\d+)", part[0])
                p = self.page_numbers.get(int(pg_match[1]), page) if pg_match else page
                mcid = re.search(r"/MCID\s+(\d+)", part[0])
                obj = re.search(r"/Obj\s+(\d+)", part[0])
                if obj:
                    annotations.append((p, int(obj[1])))
                child = mark_on(p, mcid[1]) if mcid else None
            if child is not None:
                children.append(child)
        node = {"role": role, "children": children, "xref": xref}
        if role == "Figure" and page:
            box_type, raw_box = doc.xref_get_key(xref, "A/BBox")
            box = [float(v) for v in raw_box.strip("[]").split()] if box_type == "array" else None
            if box:
                box = list(fitz.Rect(box) * doc[page - 1].transformation_matrix)
            else:
                boxes = [b for c in children for b in c.get("image_boxes", [])]
                if boxes:
                    box = [min(b[0] for b in boxes), min(b[1] for b in boxes),
                           max(b[2] for b in boxes), max(b[3] for b in boxes)]
            if box:
                node["figure"] = self.image(page, box)
                node["page"] = page
                node["box"] = box
                alt_type, alt = doc.xref_get_key(xref, "Alt")
                if alt_type == "string":
                    node["alt"] = alt
        if role in {"TD", "TH"}:
            _, attrs = doc.xref_get_key(xref, "A")
            for attr in ("ColSpan", "RowSpan"):
                match = re.search(rf"/{attr}\s+(\d+)", attrs)
                if match and int(match[1]) > 1:
                    node[attr] = int(match[1])
        if role == "Link" and annotations:
            for p, obj in annotations:
                if not p:
                    continue
                for link in self.doc[p - 1].get_links():
                    if link["xref"] != obj:
                        continue
                    if link["kind"] == fitz.LINK_URI:
                        node["url"] = link.get("uri")
                    elif link["kind"] == fitz.LINK_GOTO:
                        node["target_page"] = link["page"] + 1
                    elif link["kind"] == fitz.LINK_NAMED:
                        node["target_page"] = self.named_page(link.get("nameddest"))
                    break
        return node

    def run(self):
        self.read_marks()
        root = self.visit(first_number(self.doc.xref_get_key(self.doc.pdf_catalog(), "StructTreeRoot")[1]))
        unused = [(page, mark, value["text"][:110]) for (page, mark), value in self.marked.items()
                  if (page, mark) not in self.used and value["text"].strip() and page not in (5, 6)]
        print(f"{len(self.doc)} pages, {len(self.marked)} marked items, {len(unused)} unused text marks outside TOC")
        if unused:
            print(unused[:25])
        return {"source": self.source.name, "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                "pages": len(self.doc), "toc": self.doc.get_toc(), "root": root,
                "unused": unused}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("data", type=Path)
    parser.add_argument("assets", type=Path)
    args = parser.parse_args()
    data = Extraction(args.pdf, args.assets).run()
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.data.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


if __name__ == "__main__":
    main()
