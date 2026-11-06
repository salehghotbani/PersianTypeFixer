"""Check static site metadata, JSON-LD, local assets, and navigation targets."""
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'docs'
CANONICAL = 'https://salehghotbani.github.io/PersianTypeFixer/'


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.h1s = 0
        self.metadata = {}
        self.canonical = None
        self.structured = []
        self.in_json = False

    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        if tag == 'html':
            assert a.get('lang') == 'fa' and a.get('dir') == 'rtl'
        if 'id' in a:
            assert a['id'] not in self.ids, f"Duplicate id: {a['id']}"
            self.ids.add(a['id'])
        if tag == 'h1': self.h1s += 1
        if tag == 'meta': self.metadata[a.get('name', a.get('property'))] = a.get('content')
        if tag == 'link' and a.get('rel') == 'canonical': self.canonical = a['href']
        for key in ('href', 'src'):
            if key in a: self.links.append(a[key])
        if tag == 'script' and a.get('type') == 'application/ld+json': self.in_json = True

    def handle_data(self, data):
        if self.in_json: self.structured.append(json.loads(data))

    def handle_endtag(self, tag):
        if tag == 'script': self.in_json = False


def main():
    doc = Document()
    source = (ROOT / 'index.html').read_text(encoding='utf-8')
    doc.feed(source)
    assert doc.h1s == 1
    assert doc.canonical == CANONICAL
    for key in ('description', 'viewport', 'robots', 'og:title', 'og:description', 'og:image', 'twitter:card'):
        assert doc.metadata.get(key), key
    assert doc.structured[0]['@type'] == 'SoftwareApplication'
    assert doc.structured[0]['url'] == CANONICAL
    for link in doc.links:
        url = urlsplit(link)
        if not url.scheme and not url.netloc:
            if url.path: assert (ROOT / unquote(url.path)).is_file(), link
            if url.fragment: assert url.fragment in doc.ids, link
    assert (ROOT / 'assets/Vazirmatn.ttf').is_file()
    assert (ROOT / 'assets/OFL.txt').is_file()
    assert (ROOT / 'assets/social.png').stat().st_size > 1000
    assert CANONICAL in (ROOT / 'robots.txt').read_text()
    tree = ET.parse(ROOT / 'sitemap.xml')
    assert tree.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text == CANONICAL
    print('Site metadata, structured data, assets, anchors, RTL, robots, and sitemap passed')


if __name__ == '__main__': main()
