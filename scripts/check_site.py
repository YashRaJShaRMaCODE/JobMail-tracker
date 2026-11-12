from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1] / "site"


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.fragments = []
        self.assets = []
        self.controlled_ids = []
        self.has_main = False
        self.has_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if attrs.get("aria-controls"):
            self.controlled_ids.extend(attrs["aria-controls"].split())
        if tag == "main":
            self.has_main = True
        if tag == "title":
            self.has_title = True
        if tag == "a" and attrs.get("href", "").startswith("#"):
            self.fragments.append(attrs["href"][1:])
        if tag == "script" and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") in {"stylesheet", "icon"}:
            self.assets.append(attrs.get("href", ""))


def main():
    parser = SiteParser()
    parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
    assert parser.has_main and parser.has_title, "index needs a title and main landmark"
    assert all(fragment in parser.ids for fragment in parser.fragments), "broken in-page link"
    assert all(controlled_id in parser.ids for controlled_id in parser.controlled_ids), "broken aria-controls reference"
    assert {"sample-rows-toggle", "sample-rows", "sample-copy", "sample-copy-status"} <= parser.ids, "sample sheet preview controls are missing"
    assert all((ROOT / asset).is_file() for asset in parser.assets), "missing local asset"
    assert not any(asset.startswith(("http://", "https://")) for asset in parser.assets), "remote runtime asset"
    ElementTree.parse(ROOT / "sitemap.xml")
    print("JobMail site checks passed.")


if __name__ == "__main__":
    main()
