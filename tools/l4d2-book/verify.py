"""Validate the published static book's local resources and searchable links."""
import argparse
from collections import Counter
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import html


def verify(root):
    expected = {"index.html", "front.html", "appendix.html"}
    expected.update(f"chapter-{chapter:02}.html" for chapter in range(1, 11))
    documents = {page.name: html.parse(str(page)) for page in root.glob("*.html")}
    assert expected == documents.keys(), "Missing or unexpected chapter files"
    anchors = {}
    links = []
    images = set()
    tables = 0
    for file, document in documents.items():
        ids = document.xpath("//*[@id]/@id")
        assert len(ids) == len(set(ids)), f"Duplicate anchors in {file}: {Counter(ids)}"
        anchors[file] = set(ids)
        if file != "index.html":
            assert len(document.xpath("//article")) == 1, f"Missing text article in {file}"
        covers = document.xpath("//article/figure[@class='chapter-cover']/a/img")
        assert len(covers) == int(file.startswith("chapter-")), f"Unexpected number of covers in {file}"
        for cover in covers:
            width, height = int(cover.get("width")), int(cover.get("height"))
            assert 1.40 < height / width < 1.43, f"Cover does not match the source page ratio in {file}"
            assert cover.get("src") == cover.getparent().get("href"), f"Invalid cover image link in {file}"
        assert not document.xpath("//iframe|//object|//embed|//canvas"), f"Unexpected embedded viewer in {file}"
        images.update(document.xpath("//article//img/@src"))
        tables += len(document.xpath("//article//table"))
        resources = document.xpath("//a/@href|//img/@src|//script/@src|//link[@rel='stylesheet']/@href")
        links.extend((file, link) for link in resources)
    hammer_chapter = documents["chapter-01.html"]
    figure = hammer_chapter.xpath("//figure[@id='figure-1-4-1']/a/img")
    assert len(figure) == 1, "Missing annotated Hammer figure"
    assert 1.47 < int(figure[0].get("width")) / int(figure[0].get("height")) < 1.49, (
        "Hammer figure crop must include the right-side callouts"
    )
    assert hammer_chapter.xpath("//p/a[@href='./chapter-01.html#figure-1-4-1']"), "Broken Hammer figure cross-reference"
    search_file = (root / "search-data.js").read_text(encoding="utf-8").strip()
    records = json.loads(search_file.removeprefix("window.BOOK_SEARCH = ").removesuffix(";"))
    links.extend(("index.html", row[0]) for row in records)
    for origin, link in links:
        url = urlsplit(link)
        if url.scheme:
            continue
        resource = unquote(url.path) or origin
        assert (root / resource).is_file(), f"Missing resource {link} from {origin}"
        resource_name = Path(resource).name
        if url.fragment and resource_name in anchors:
            assert unquote(url.fragment) in anchors[resource_name], f"Missing target {link} from {origin}"
    assert len(documents["appendix.html"].xpath("//div[@class='term-index']/p")) >= 75, "Missing term index"
    assert len(documents["chapter-10.html"].xpath("//table[1]//tr[td]")) >= 250, "Incomplete entity table"
    assert len(documents["index.html"].xpath("//div[@class='contents-detail']//li/a")) == 141, "Incomplete book contents"
    for ref in documents["index.html"].xpath("//div[@class='contents-detail']//li/a/@href"):
        url = urlsplit(ref)
        file = Path(url.path).name
        assert documents[file].xpath("//article//*[self::h2 or self::h3][@id=$target]",
                                     target=url.fragment), f"Section lacks heading: {ref}"
    print(f"{len(documents)} HTML files, {len(links)} resource or anchor references, "
          f"{len(images)} illustrations, {tables} tables and {len(records)} search entries verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    verify(parser.parse_args().directory)
