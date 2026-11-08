"""Build a static Chinese web book from the tagged source representation."""
import argparse
import json
import re
import shutil
import unicodedata
from collections import Counter
from html import escape
from pathlib import Path

from lxml import html as lxml_html

TITLE = "精通求生之路地图制作"
SUBTITLE = "从入门到发布"
FULL = f"{TITLE}：{SUBTITLE}"
VERSION = "v0.8.1"
CANONICAL = "https://docs.dakang233.com/l4d2-book/"
EXTERNAL_URL = re.compile(r"https?://[^\s<>\u3000-\u9fff（）。，；「」『』]+")
SECTION_NUMBER = re.compile(r"^(\d+(?:\.\d+)+)(?![\d.])")
CHAPTER_NUMBER = re.compile(r"^第\s*(\d+)\s*章")
EXERCISE_NUMBER = re.compile(r"^习题\s*(\d+)(?:\s|$)")


def keys(text):
    return re.sub(r"[\s\u2000-\u200f\x08]", "", unicodedata.normalize("NFKC", text)).casefold()


def text_of(node):
    if "text" in node:
        return node["text"]
    if node.get("role") in {"Figure", "Note"}:
        return ""
    return "".join(text_of(c) for c in node.get("children", []))


def page_of(node):
    if node.get("page"):
        return node["page"]
    return next((p for c in node.get("children", []) if (p := page_of(c))), None)


def visible(text):
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\u200b]", "", text)


def clean_title(text):
    text = re.sub(r"\s+", " ", visible(text)).strip()
    return re.sub(r"^(\d+(?:\.\d+)+)(?=[^\d.\s])", r"\1 ", text)


def local_page(page):
    return f"page-{page - 6}" if page > 6 else f"front-{page}"


def join_space(left, right):
    return bool(re.search(r"[A-Za-z0-9.,:;!?)]$", left) and re.match(r"[A-Za-z0-9(]", right)
                and not re.search(r"[/_\\-]$", left))


def plain_linked(text):
    last = 0
    pieces = []
    for m in EXTERNAL_URL.finditer(text):
        url = m[0].rstrip(".,;")
        while url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        pieces += [escape(text[last:m.start()]), f'<a href="{escape(url, quote=True)}">{escape(url)}</a>']
        last = m.start() + len(url)
    pieces.append(escape(text[last:]))
    return "".join(pieces)


def image_tag(figure, alt, css=""):
    return (
        f'<img src="./figures/{figure["asset"]}" width="{figure["width"]}" height="{figure["height"]}"'
        f' alt="{escape(alt, quote=True)}" loading="lazy" decoding="async"'
        f' class="{css}" style="--figure-width:{max(25, round(figure["display"] * 1.65))}px">'
    )


class Renderer:
    def __init__(self, data):
        self.data = data
        self.toc = data["toc"]
        self.chapter_covers = {int(page): image for page, image in data["chapter_covers"].items()}
        self.bookmarks = {(page, keys(title)): (level, clean_title(title)) for level, title, page in self.toc}
        self.parts = [
            {"id": "front", "label": "卷首", "title": "前言与出版信息", "page": 1, "nodes": []}
        ]
        for level, title, page in self.toc:
            if level == 1:
                match = CHAPTER_NUMBER.match(title)
                slug = f'chapter-{int(match[1]):02}' if match else "appendix"
                self.parts.append({"id": slug, "label": f'第 {match[1]} 章' if match else "附录",
                                   "title": re.sub(r"^第\s*\d+\s*章\s*", "", title).strip(),
                                   "page": page, "nodes": []})
        self.by_page = {page: next(part for part in reversed(self.parts) if part["page"] <= page)
                        for page in range(1, data["pages"] + 1)}
        article = data["root"]["children"][0]["children"][0]["children"]
        for story in article:
            if story["role"] != "Story":
                continue
            for node in story["children"]:
                page = page_of(node)
                if page and page not in {1, 4, 5, 6, data["pages"]}:
                    self.by_page[page]["nodes"].extend(self.normalize_blocks(node))
        front = self.parts[0]["nodes"]
        front.sort(key=lambda n: page_of(n) or 1)
        self.notes_by_page = {}
        self.note_targets = {}
        for part in self.parts:
            for node in part["nodes"]:
                self.collect_notes(node)
        self.headings = {}
        self.bookmark_ids = {}
        self.figures = set()
        self.counts = Counter()
        for part in self.parts:
            for node in part["nodes"]:
                info = self.heading(node)
                if info:
                    self.headings[node["xref"]] = info
                    if info.get("bookmark"):
                        self.bookmark_ids[info["bookmark"]] = (part["id"], info["id"])

    def normalize_blocks(self, node):
        role = node["role"]
        if role == "Index":
            children = node["children"]
            if children and children[0].get("role") == "L":
                items = children[0]["children"]
                if items:
                    title = {**items[0], "role": "list-heading"}
                    if self.heading(title):
                        return [title, {**node, "children": items[1:]}]
            return [node]
        if role != "L":
            return [node]
        blocks = []
        group = []

        def flush():
            if group:
                blocks.append({**node, "children": group.copy()})
                group.clear()

        for item in node["children"]:
            if item.get("role") != "LI":
                group.append(item)
                continue
            title = []
            suffix = []
            for child in item["children"]:
                if child.get("role") == "Lbl":
                    title.append(child)
                elif child.get("role") == "LBody":
                    for inner in child["children"]:
                        if inner.get("role") in {"Sect", "Figure", "L", "Table", "Story", "Note"}:
                            suffix.append(inner)
                        else:
                            title.append(inner)
                else:
                    suffix.append(child)
            candidate = {**item, "role": "list-heading", "children": title}
            if self.heading(candidate):
                flush()
                blocks.append(candidate)
                for child in suffix:
                    blocks.extend(self.normalize_blocks(child) if child["role"] == "L" else [child])
            else:
                group.append(item)
        flush()
        return blocks

    def heading(self, node):
        role = node["role"]
        page = page_of(node)
        title = clean_title(text_of(node))
        if role == "list-heading":
            # Exclude superscript note markers from bookmark matching.
            def without_note(n):
                if n.get("role") in {"Note", "Reference"} or n.get("font") == "footnote-marker":
                    return ""
                if "text" in n:
                    return n["text"]
                return "".join(without_note(c) for c in n["children"])
            title = clean_title(without_note(node))
        if not title or len(title) > 110:
            return None
        normalized = keys(title)
        bookmark = (page, normalized)
        match = self.bookmarks.get(bookmark)
        number = SECTION_NUMBER.match(title)
        if number and self.by_page[page]["id"] != f"chapter-{int(number[1].split('.')[0]):02}":
            number = None
        chapter = CHAPTER_NUMBER.match(title)
        exercise = EXERCISE_NUMBER.match(title)
        part = self.by_page[page]
        if not match and (number or exercise or chapter):
            pattern = SECTION_NUMBER if number else EXERCISE_NUMBER if exercise else CHAPTER_NUMBER
            n = (number or exercise or chapter)[1]
            for level, label, p in self.toc:
                m = pattern.match(label)
                if p == page and m and m[1] == n and (
                    role.startswith(("一级段落", "二级段落")) or role == "list-heading" or normalized == keys(label)
                ):
                    bookmark = (p, keys(label))
                    match = (level, clean_title(label))
                    break
        if match:
            level, title = match
        elif role == "标题" and title == "前言":
            level = 1
        elif (role.startswith(("一级段落", "二级段落")) or role == "list-heading") and (number or chapter):
            level = 1 if chapter else 2 if number[1].count(".") == 1 else 3
        elif "二级段落-无编号" in role and not re.match(r"[（(]?[一二三四五六七八九十\d]+[）)、.]", title):
            level = 2
        else:
            return None
        if chapter and level == 1 or title == "附录" and level == 1:
            anchor = part["id"]
        elif number:
            anchor = "section-" + number[1].replace(".", "-")
        elif exercise:
            anchor = "exercise-" + exercise[1]
        elif title == "前言":
            anchor = "preface"
        else:
            anchor = {
                "视频资源": "videos", "作图圈现状": "community", "鸣谢名单": "credits",
                "习题之参考答案": "answers", "适用于求生之路2的导航网格编辑模式配置文件": "nav-config",
                "部分名词释义": "glossary", "中国求生之路地图作者及其作品列表": "map-authors",
                "部分名词索引": "term-index",
            }.get(title, "heading-" + str(node["xref"]))
        return {"title": title, "level": level, "id": anchor, "page": page, "bookmark": bookmark if match else None}

    def page_url(self, page):
        part = self.by_page.get(page)
        if not part:
            return None
        if page <= 1 or page in {4, 5, 6} or page == self.data["pages"]:
            return "./index.html#contents"
        return f'./{part["id"]}.html#{local_page(page)}'

    def page_mark(self, page):
        if self.part["id"] != self.by_page[page]["id"] or page in self.seen_pages:
            return ""
        self.seen_pages.add(page)
        return f'<span class="page-anchor" id="{local_page(page)}"></span>'

    def caption(self, node):
        txt = clean_title(text_of(node))
        return bool(re.match(r"^(图|表)\s*\d+[-－–.]\d+", txt))

    def figure(self, node, inline=False, alt=""):
        asset = node.get("figure")
        if not asset:
            return ""
        self.figures.add(asset["asset"])
        self.counts["figures"] += 1
        alt = node.get("alt") or alt
        img = image_tag(asset, alt, "inline-image" if inline else "book-image")
        if inline:
            return img
        return f'<a href="./figures/{asset["asset"]}" class="figure-link" aria-label="查看原图{("：" + escape(alt, quote=True)) if alt else ""}">{img}</a>'

    def runs(self, node, inline=True):
        if "text" in node:
            return [(node, None)]
        role = node["role"]
        if role == "Figure":
            return [(None, self.figure(node, inline))]
        if role == "Note":
            return []
        kids = [r for c in node["children"] for r in self.runs(c, inline)]
        if role == "Link" and (node.get("url") or node.get("target_page")):
            href = node.get("url") or self.page_url(node.get("target_page"))
            if href and (href.startswith(("./", "https://", "http://", "mailto:"))):
                content = self.flow(kids, link_urls=False)
                if content.strip():
                    return [(None, f'<a href="{escape(href, quote=True)}">{content}</a>')]
        return kids

    def flow(self, runs, preserve_lines=False, raw=False, link_urls=True):
        pieces = []
        buffer = []
        previous = None

        def flush():
            if buffer:
                text = "".join(buffer)
                pieces.append(text if raw else plain_linked(text) if link_urls else escape(text))
                buffer.clear()

        for mark, rendered in runs:
            if mark is None:
                if rendered:
                    flush()
                    pieces.append(rendered)
                continue
            value = visible(mark["text"])
            if not value:
                continue
            if not raw and mark["page"] not in self.seen_pages:
                page_marker = self.page_mark(mark["page"])
                if page_marker:
                    flush()
                    pieces.append(page_marker)
            new_line = previous and (mark["page"] != previous["page"] or (
                mark["base"] is not None and previous["base"] is not None
                and abs(mark["base"] - previous["base"]) >= 5.8
                and mark["box"][0] < previous["box"][2] - 1
                and mark["font"] != "footnote-marker" and previous["font"] != "footnote-marker"
            ))
            if new_line:
                if preserve_lines:
                    flush()
                    pieces.append("\n" if raw else "<br>")
                elif not raw and not previous["text"].endswith((" ", "\u3000")) and join_space(previous["text"], value):
                    buffer.append(" ")
            elif previous and previous["box"] and mark["box"] and mark["page"] == previous["page"]:
                gap = mark["box"][0] - previous["box"][2]
                if gap > 2 and not (previous["text"].endswith((" ", "\u3000")) or value.startswith(" ")):
                    if preserve_lines and gap > 18:
                        flush()
                        pieces.append("\n" if raw else "<br>")
                    elif not raw and (join_space(previous["text"], value) or gap > 6):
                        buffer.append(" ")
            if not raw and mark["font"] == "footnote-marker":
                flush()
                ref = self.note_targets.get((mark["page"], value.strip()))
                marker = f'<a href="#{ref}">{escape(value)}</a>' if ref else escape(value)
                pieces.append(f'<sup>{marker}</sup>')
            else:
                buffer.append(value)
            previous = mark
        flush()
        result = "".join(pieces)
        return result.rstrip() if raw else result.strip()

    def collect_notes(self, node):
        role = node.get("role", "")
        if role == "Note" or role.startswith("脚注"):
            text = text_of(node) if role != "Note" else "".join(text_of(c) for c in node["children"])
            page = page_of(node)
            if page and text.strip():
                notes = self.notes_by_page.setdefault(page, {})
                if keys(text) not in notes:
                    ident = f'note-{page}-{len(notes) + 1}'
                    notes[keys(text)] = (ident, text)
                    match = re.match(r"\s*([a-z])", text)
                    if match:
                        self.note_targets.setdefault((page, match[1]), ident)
            return
        for child in node.get("children", []):
            self.collect_notes(child)

    def chapter_notes(self, part):
        entries = []
        for page, notes in sorted(self.notes_by_page.items()):
            if self.by_page[page] is part:
                label = f"原书第 {page - 6} 页" if page > 6 else "卷首"
                for ident, text in notes.values():
                    entries.append(f'<li id="{ident}"><a href="#{local_page(page)}">{label}</a> {plain_linked(visible(text))}</li>')
        if not entries:
            return ""
        return '<section class="chapter-notes" aria-label="原书脚注"><h2>原书脚注</h2><ol>' + "".join(entries) + '</ol></section>'

    def table(self, node):
        groups = []
        for group in node["children"]:
            role = group.get("role")
            if role not in {"THead", "TBody", "TFoot", "TR"}:
                continue
            name = {"THead": "thead", "TBody": "tbody", "TFoot": "tfoot", "TR": "tbody"}[role]
            rows = [group] if role == "TR" else group["children"]
            if rows:
                groups.append((name, rows))
        # InDesign stores a table's body before its header in the tag tree.
        # Multiple page fragments may have their own repeated header.
        groups.sort(key=lambda item: min((page_of(r) or 999 for r in item[1]), default=999))
        self.counts["tables"] += 1
        output = []
        for group_type, rows in groups:
            for index, row in enumerate(rows):
                if not row.get("children") or not page_of(row):
                    continue
                is_header = group_type == "thead" or (
                    index == 0 and text_of(row["children"][0]).strip() in
                    {"值", "编号", "序号", "按键", "命令", "测试名称", "名称", "中文", "游戏", "项目", "网格", "单位"}
                )
                page = page_of(row)
                cells = []
                for cell in row.get("children", []):
                    role = cell.get("role")
                    if role not in {"TD", "TH"}:
                        continue
                    tag = "th" if role == "TH" or is_header else "td"
                    attrs = "".join(f' {k.lower()}="{cell[k]}"' for k in ("ColSpan", "RowSpan") if k in cell)
                    if not cells and page:
                        marker = self.page_mark(page)
                    else:
                        marker = ""
                    paragraphs = []
                    for c in cell["children"]:
                        if c.get("role") in {"Table", "L"}:
                            v = self.block(c)
                        else:
                            v = self.flow(self.runs(c))
                        if v:
                            paragraphs.append(v)
                    value = "<br>".join(paragraphs) if all(c.get("role") not in {"Span", None} for c in cell["children"]) else self.flow(self.runs(cell))
                    cells.append(f'<{tag}{attrs}>{marker}{value}</{tag}>')
                if cells:
                    self.counts["rows"] += 1
                    output.append(f'<tr id="row-{row["xref"]}">{"".join(cells)}</tr>')
        if not output:
            return ""
        return '<div class="table-scroll" tabindex="0" aria-label="表格，可横向滚动"><table><tbody>' + "".join(output) + "</tbody></table></div>"

    def list(self, node):
        items = []
        for item in node.get("children", []):
            if item.get("role") != "LI":
                continue
            label, body = "", []
            for child in item["children"]:
                if child.get("role") == "Lbl":
                    label = self.flow(self.runs(child))
                    if label in {"\ufffd", "(cid:0)"} or re.search(r"\(cid:\d+\)", label):
                        label = "•"
                elif child.get("role") == "L":
                    body.append(self.list(child))
                elif child.get("role") == "LBody" and not any(c.get("role") in {"Table", "L", "Sect"} for c in child["children"]):
                    preserve = any(c.get("role") == "选择题选项-基线" for c in child["children"])
                    body.append(self.flow(self.runs(child), preserve_lines=preserve))
                else:
                    body.append(self.block(child, in_list=True))
            if label or any(body):
                items.append(f'<li><span class="list-label">{label or "•"}</span><div>{"".join(body)}</div></li>')
        return f'<ul class="book-list" role="list">{"".join(items)}</ul>' if items else ""

    def block(self, node, in_list=False):
        role = node.get("role")
        if not role:
            return self.flow(self.runs(node))
        if role == "L":
            return self.list(node)
        if role == "Table":
            return self.table(node)
        if role == "Index":
            return self.index(node)
        if role == "Figure":
            figure = self.figure(node, inline=in_list)
            return figure if in_list or not figure else f"<figure>{figure}</figure>"
        if role == "Note" or role.startswith("脚注"):
            return ""
        if node["xref"] in self.headings:
            heading = self.headings[node["xref"]]
            if heading["id"] == self.part["id"]:
                return ""
            h = max(2, heading["level"])
            anchor = heading["id"]
            return (f'<h{h} id="{anchor}">{escape(heading["title"])}'
                    f'<a class="heading-link" href="#{anchor}" aria-label="本节链接">#</a></h{h}>')
        if role == "Sect" and any(c.get("role") == "Figure" for c in node["children"]):
            captions = [c for c in node["children"] if c.get("role") != "Figure"]
            caption = " ".join(self.flow(self.runs(c)) for c in captions).strip()
            alt = " ".join(clean_title(text_of(c)) for c in captions).strip()
            figures = "".join(self.figure(c, alt=alt) for c in node["children"] if c.get("role") == "Figure")
            return f'<figure>{figures}' + (f'<figcaption>{caption}</figcaption>' if caption else "") + '</figure>'
        if any(c.get("role") in {"Table", "Sect", "L"} for c in node["children"]):
            fragments = []
            inline_run = []
            for child in node["children"]:
                if child.get("role") in {"Table", "Sect", "L"}:
                    if inline_run and (text := self.flow(inline_run)):
                        fragments.append(f"<p>{text}</p>")
                    inline_run.clear()
                    fragments.append(self.block(child))
                else:
                    inline_run.extend(self.runs(child))
            if inline_run and (text := self.flow(inline_run)):
                fragments.append(f"<p>{text}</p>")
            return "".join(fragments)
        content = self.flow(self.runs(node), preserve_lines=role in {"选择题选项", "选择题选项-基线"})
        if not content:
            return ""
        if in_list:
            return content
        if role.startswith(("注意", "警告", "一般注释")):
            tag, css = "aside", "callout"
        elif role.startswith("章节描述"):
            tag, css = "p", "chapter-intro"
            if page_of(node) in self.chapter_covers:
                css += " sr-only"
        elif role == "五号引文":
            tag, css = "blockquote", ""
        elif self.caption(node):
            tag, css = "p", "caption"
        else:
            tag, css = "p", ""
        return f'<{tag}{f" class={css!r}" if css else ""}>{content}</{tag}>'

    def index(self, node):
        if node["role"] == "Index":
            return '<div class="term-index">' + "".join(self.index(c) for c in node["children"]) + "</div>"
        label = clean_title(text_of(node))
        runs = self.runs(node)
        rendered = self.flow(runs)
        match = re.fullmatch(r"(.*?)\s+(\d{1,3})", label)
        if match and match[1] and 1 <= int(match[2]) <= self.data["pages"] - 7:
            printed = match[2]
            href = self.page_url(int(printed) + 6)
            # Source index links are embedded in the tags when present.
            if "<a " not in rendered and rendered.endswith(printed):
                rendered = rendered[:-len(printed)].rstrip() + f' <a href="{href}">{printed}</a>'
        if not rendered:
            return ""
        page = page_of(node)
        marker = self.page_mark(page) if page else ""
        if len(label) == 1 or label in {"中文", "罗马字"}:
            return f'{marker}<h3>{rendered}</h3>'
        return f'{marker}<p>{rendered}</p>'

    def code(self, nodes):
        lines = []
        for node in nodes:
            line = self.flow(self.runs(node), raw=True)
            lines.append(line)
        self.counts["code"] += 1
        return f'<div class="code-block"><pre><code>{escape(chr(10).join(lines))}</code></pre></div>'

    def content(self, part):
        self.part = part
        self.seen_pages = set()
        body = []
        page = part["page"]
        if cover := self.chapter_covers.get(page):
            alt = f'{part["label"]} {part["title"]}，原书章节封面'
            image = self.figure({"figure": cover}, alt=alt)
            body.append(self.page_mark(page) + f'<figure class="chapter-cover">{image}</figure>')
        nodes = part["nodes"]
        i = 0
        while i < len(nodes):
            node = nodes[i]
            page = page_of(node)
            marker = self.page_mark(page) if page else ""
            if part["id"] == "front" and page == 2 and marker:
                marker += '<h2 id="publication">出版信息</h2>'
            if node["role"].startswith("代码"):
                end = i + 1
                while end < len(nodes) and nodes[end]["role"].startswith("代码"):
                    next_page = page_of(nodes[end])
                    if next_page:
                        marker += self.page_mark(next_page)
                    end += 1
                body.append(marker + self.code(nodes[i:end]))
                i = end
                continue
            if i + 1 < len(nodes) and self.caption(nodes[i + 1]) and page_of(nodes[i + 1]) == page:
                figures = [c for c in node["children"] if c.get("role") == "Figure"] if node["role"] == "图片" else [node] if node["role"] == "Figure" else []
                if figures:
                    caption = self.flow(self.runs(nodes[i + 1]))
                    alt = clean_title(text_of(nodes[i + 1]))
                    images = "".join(self.figure(figure, alt=alt) for figure in figures)
                    body.append(marker + f"<figure>{images}<figcaption>{caption}</figcaption></figure>")
                    i += 2
                    continue
            if node["role"] == "图片":
                figures = [c for c in node["children"] if c.get("role") == "Figure"]
                if figures:
                    body.append(marker + f'<figure>{"".join(self.figure(figure) for figure in figures)}</figure>')
                    i += 1
                    continue
            body.append(marker + self.block(node))
            i += 1
        # Page links from the printed index remain valid on continuation pages.
        missing = [p for p, owner in self.by_page.items() if owner is part and p not in self.seen_pages and p not in {1, 4, 5, 6, self.data["pages"]}]
        if missing:
            print(f'Pages with no dedicated text anchor in {part["id"]}: {missing}')
            body.extend(self.page_mark(page) for page in missing)
        return "\n".join(body) + self.chapter_notes(part)

    def contents(self):
        rows = []
        for part in self.parts[1:]:
            links = []
            for level, label, page in self.toc:
                if level == 1 or self.by_page[page] is not part:
                    continue
                target = self.bookmark_ids.get((page, keys(label)))
                href = f'./{target[0]}.html#{target[1]}' if target else self.page_url(page)
                links.append(f'<li class="toc-level-{level}"><a href="{href}">{escape(clean_title(label))}</a></li>')
            rows.append(
                f'<details class="contents-row"><summary><span class="chapter-label">{part["label"]}</span>'
                f'<span>{escape(part["title"] if part["id"] != "appendix" else "工具与参考资料")}</span></summary><div class="contents-detail">'
                f'<a class="chapter-read" href="./{part["id"]}.html">阅读本章 <span aria-hidden="true">→</span></a>'
                f'<ul>{"".join(links)}</ul></div></details>'
            )
        return "\n".join(rows)

    def chapter_nav(self, part):
        links = []
        for chapter in self.parts:
            current = ' aria-current="page"' if part is chapter else ""
            links.append(f'<li><a href="./{chapter["id"]}.html"{current}>'
                         f'<span>{chapter["label"]}</span>{escape(chapter["title"] if chapter["id"] != "appendix" else "工具与参考资料")}</a></li>')
        return '<ul class="chapter-nav">' + "".join(links) + "</ul>"

    def section_nav(self, part):
        links = [f'<li class="toc-level-{h["level"]}"><a href="#{h["id"]}">{escape(h["title"])}</a></li>'
                 for h in self.headings.values()
                 if self.by_page[h["page"]] is part and h["id"] != part["id"]]
        return f'<ul>{"".join(links)}</ul>' if links else ""

    def report(self):
        missing = [title for level, title, page in self.toc if (page, keys(title)) not in self.bookmark_ids]
        print("Output:", dict(self.counts))
        print(f"{len(self.bookmark_ids)}/{len(self.toc)} bookmarks link directly to headings")
        if missing:
            print("Bookmarks using page fallback:", missing)


def shell(title, page, body, css=""):
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{escape(title, quote=True)}。大康编著的求生之路 2 地图制作教程。">
<link rel="canonical" href="{CANONICAL + (page if page != 'index.html' else '')}">
<link rel="stylesheet" href="./book.css">
<title>{escape(title)}</title>
<script defer src="./search-data.js"></script>
<script defer src="./book.js"></script>
</head>
<body class="{css}">
<a class="skip-link" href="#main">跳到正文</a>
<header class="topbar">
  <div class="topbar-inner"><a class="wordmark" href="./index.html"><span aria-hidden="true" class="brand-icon">▦</span><span>大康233<span class="brand-sep"> / </span><span class="brand-book">地图制作手册</span></span></a>
    <nav aria-label="站点导航"><a href="./index.html#contents">全书目录</a><button type="button" id="open-search" aria-haspopup="dialog" hidden><span aria-hidden="true">⌕</span> <span>搜全书</span> <kbd>Ctrl K</kbd></button></nav>
  </div>
</header>
{body}
<footer class="site-footer"><div><span>大康233 · {TITLE}</span><span>网页读本 · {VERSION}</span></div></footer>
<dialog id="search" aria-labelledby="search-title">
  <div class="dialog-head"><h2 id="search-title">搜索全书</h2><form method="dialog"><button type="submit" aria-label="关闭搜索">×</button></form></div>
  <label for="search-input" class="sr-only">搜索词</label><input id="search-input" type="search" placeholder="章节、命令、实体名…" autocomplete="off">
  <p id="search-status" role="status"></p><ol id="search-results"></ol>
</dialog>
</body>
</html>
"""


def home(renderer):
    hero = """<div class="hero-visual" aria-hidden="true"><div class="blueprint"></div><div class="plan plan-a"></div><div class="plan plan-b"></div><div class="plan plan-c"></div><div class="axis">Y<br>└──── X</div><div class="visual-note">SOURCE ENGINE<br>HAMMER / LEVEL EDITOR</div></div>"""
    return shell(FULL, "index.html", f"""
<main id="main">
  <section class="hero">
    <div class="hero-inner">
      <div class="hero-copy"><p class="eyebrow"><span></span> LEFT 4 DEAD 2 · 制图教程</p>
        <h1>{TITLE}<small>{SUBTITLE}</small></h1>
        <p class="hero-description">从认识起源引擎和 Hammer，到搭建第一张地图、编辑导航网格、编写脚本与优化关卡。</p>
        <div class="hero-actions"><a class="primary" href="./chapter-01.html">开始阅读 <span aria-hidden="true">→</span></a><a class="hero-secondary" href="#contents">浏览目录</a></div>
        <div class="edition"><span>大康 编</span><span>2026 年 6 月第一版</span><span>{VERSION}</span></div>
      </div>
      {hero}
    </div>
  </section>
  <section class="home-contents" id="contents">
    <div class="contents-heading"><p class="eyebrow"><span></span> TABLE OF CONTENTS</p><h2>全书目录</h2><p>10 章 · 附录、习题与参考答案</p></div>
    <a class="front-link" href="./front.html"><span>卷首</span><strong>前言与出版信息</strong><span aria-hidden="true">→</span></a>
    {renderer.contents()}
    <p class="edition-note">底本为 2026 年 6 月 14 日导出的 {VERSION}。原书中的编写进度标记保留在各章正文中。</p>
  </section>
</main>""", "home")


def chapter(renderer, part, body):
    index = renderer.parts.index(part)
    prev = renderer.parts[index - 1] if index else None
    following = renderer.parts[index + 1] if index + 1 < len(renderer.parts) else None
    prev_link = f'<a href="./{prev["id"]}.html"><small>← 上一篇</small>{escape(prev["title"])}</a>' if prev else '<a href="./index.html#contents"><small>← 返回</small>全书目录</a>'
    next_link = f'<a href="./{following["id"]}.html"><small>下一篇 →</small>{escape(following["title"])}</a>' if following else ""
    sections = renderer.section_nav(part)
    mobile_sections = f'<details class="mobile-sections"><summary>本篇目录</summary>{sections}</details>' if sections else ""
    right = f'<aside class="section-sidebar"><nav aria-label="本篇目录"><h2>本篇目录</h2>{sections}</nav></aside>' if sections else ""
    title = f'{part["title"]} · {TITLE}'
    return shell(title, part["id"] + ".html", f"""
<div class="reader-layout">
  <aside class="book-sidebar"><nav aria-label="全书章节"><h2>全书章节</h2>{renderer.chapter_nav(part)}</nav></aside>
  <main id="main">
    <div class="chapter-header" id="{part["id"]}"><div class="breadcrumb"><a href="./index.html#contents">全书目录</a><span aria-hidden="true">/</span>{part["label"]}</div><h1>{escape(part["title"])}</h1></div>
    {mobile_sections}
    <article class="book-content" aria-label="{escape(part["title"], quote=True)}">{body}</article>
    <nav class="chapter-pager" aria-label="相邻篇章">{prev_link}{next_link}</nav>
  </main>
  {right}
</div>""")


def search_records(part, body):
    root = lxml_html.fragment_fromstring(body, create_parent="article")
    records = []
    heading = part["title"]
    anchor = part["id"]
    for child in root:
        if child.tag in {"h2", "h3"}:
            heading = " ".join(child.text_content().rstrip("#").split())
            anchor = child.get("id", anchor)
            records.append([f'./{part["id"]}.html#{anchor}', part["label"], heading, ""])
            continue
        for row in child.xpath(".//tr"):
            value = " ".join(" ".join(td.text_content().split()) for td in row).strip()
            if value:
                records.append([f'./{part["id"]}.html#{row.get("id")}', part["label"], heading, value])
        if child.get("class") == "table-scroll":
            continue
        value = " ".join(child.text_content().split())
        if value:
            records.append([f'./{part["id"]}.html#{anchor}', part["label"], heading, value])
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--assets", type=Path, required=True, help="Directory of extracted WebP figures")
    args = parser.parse_args()
    renderer = Renderer(json.loads(args.data.read_text(encoding="utf-8")))
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for part in renderer.parts:
        body = renderer.content(part)
        (output / f'{part["id"]}.html').write_text(chapter(renderer, part, body), encoding="utf-8")
        records.append([f'./{part["id"]}.html', part["label"], part["title"], ""])
        records.extend(search_records(part, body))
    (output / "index.html").write_text(home(renderer), encoding="utf-8")
    (output / "search-data.js").write_text(
        "window.BOOK_SEARCH = " + json.dumps(records, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    figures = output / "figures"
    figures.mkdir(exist_ok=True)
    for name in renderer.figures:
        shutil.copyfile(args.assets / name, figures / name)
    for file in figures.glob("*.webp"):
        if re.fullmatch(r"[a-f0-9]{20}\.webp", file.name) and file.name not in renderer.figures:
            file.unlink()
    for static in ("book.css", "book.js"):
        shutil.copyfile(Path(__file__).parent / static, output / static)
    renderer.report()
    print(f"{len(records)} search records, {len(renderer.figures)} unique used figures")


if __name__ == "__main__":
    main()
