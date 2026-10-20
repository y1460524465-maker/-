"""Structural tests for the single-file AI 工作台 page."""

from html.parser import HTMLParser
from pathlib import Path
import unittest


INDEX_PATH = Path(__file__).resolve().parents[1] / "index.html"


class IndexParser(HTMLParser):
    """Collect the page structure and inline content without third-party tools."""

    VOID_ELEMENTS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.stack = []
        self.open_ids = []
        self.text_by_id = {}
        self.title = ""
        self.h1_texts = []
        self.h3_texts = []
        self.script_text = ""
        self.style_text = ""
        self.cards = []

        self._title_parts = None
        self._h1_parts = None
        self._h3_parts = None
        self._script_parts = None
        self._style_parts = None
        self._card_stack = []

    def handle_starttag(self, tag, attrs):
        attrs = {name.lower(): (value or "") for name, value in attrs}
        self.tags.append((tag, attrs))

        if tag == "title":
            self._title_parts = []
        elif tag == "h1":
            self._h1_parts = []
        elif tag == "h3":
            self._h3_parts = []
        elif tag == "script" and "src" not in attrs:
            self._script_parts = []
        elif tag == "style":
            self._style_parts = []

        if "id" in attrs:
            self.open_ids.append((tag, attrs["id"]))
            self.text_by_id.setdefault(attrs["id"], "")

        if tag in self.VOID_ELEMENTS:
            return

        self.stack.append(tag)

        classes = attrs.get("class", "").split()
        if tag == "article" and "feature-card" in classes:
            card = {"text": ""}
            self.cards.append(card)
            self._card_stack.append((card, len(self.stack)))

    def handle_data(self, data):
        if self._title_parts is not None:
            self._title_parts.append(data)
        if self._h1_parts is not None:
            self._h1_parts.append(data)
        if self._h3_parts is not None:
            self._h3_parts.append(data)
        if self._script_parts is not None:
            self._script_parts.append(data)
        if self._style_parts is not None:
            self._style_parts.append(data)

        for _tag, element_id in self.open_ids:
            self.text_by_id[element_id] += data

        if self._card_stack:
            self._card_stack[-1][0]["text"] += data

    def handle_endtag(self, tag):
        if tag == "title" and self._title_parts is not None:
            self.title = "".join(self._title_parts).strip()
            self._title_parts = None
        elif tag == "h1" and self._h1_parts is not None:
            self.h1_texts.append("".join(self._h1_parts).strip())
            self._h1_parts = None
        elif tag == "h3" and self._h3_parts is not None:
            self.h3_texts.append("".join(self._h3_parts).strip())
            self._h3_parts = None
        elif tag == "script" and self._script_parts is not None:
            self.script_text = "".join(self._script_parts)
            self._script_parts = None
        elif tag == "style" and self._style_parts is not None:
            self.style_text = "".join(self._style_parts)
            self._style_parts = None

        if (
            tag == "article"
            and self._card_stack
            and self._card_stack[-1][1] == len(self.stack)
        ):
            self._card_stack.pop()

        for index in range(len(self.open_ids) - 1, -1, -1):
            if self.open_ids[index][0] == tag:
                del self.open_ids[index]
                break

        if tag in self.stack:
            while self.stack:
                if self.stack.pop() == tag:
                    break

    @property
    def card_texts(self):
        return [card["text"].strip() for card in self.cards]

    def attrs_for(self, tag, **match):
        """Return attribute dicts for matching tags."""
        return [
            attrs
            for found_tag, attrs in self.tags
            if found_tag == tag
            and all(attrs.get(key) == value for key, value in match.items())
        ]


class IndexPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not INDEX_PATH.is_file():
            raise AssertionError(f"Missing page: {INDEX_PATH}")
        cls.source = INDEX_PATH.read_text(encoding="utf-8")
        cls.page = IndexParser()
        cls.page.feed(cls.source)
        cls.page.close()

    def test_document_metadata_and_heading(self):
        html_tags = self.page.attrs_for("html")
        self.assertEqual(len(html_tags), 1)
        self.assertEqual(html_tags[0].get("lang"), "zh-CN")

        viewports = [
            attrs
            for tag, attrs in self.page.tags
            if tag == "meta" and attrs.get("name", "").lower() == "viewport"
        ]
        self.assertEqual(len(viewports), 1, "Expected exactly one viewport meta tag")
        viewport = viewports[0].get("content", "").lower()
        self.assertIn("width=device-width", viewport)
        self.assertIn("initial-scale=1", viewport)

        self.assertEqual(self.page.title, "AI 工作台")
        self.assertEqual(self.page.h1_texts, ["AI 工作台"])

    def test_three_feature_cards_with_expected_content(self):
        self.assertEqual(len(self.page.cards), 3)
        self.assertEqual(
            self.page.h3_texts,
            ["工作事项", "跨会话状态", "DeepSeek 执行"],
        )
        for card_text in self.page.card_texts:
            self.assertGreater(len(card_text), 20, "Each card needs an introduction")

    def test_button_and_status_ids(self):
        self.assertIn("start-button", self.page.text_by_id)
        self.assertIn("start-status", self.page.text_by_id)
        self.assertEqual(
            self.page.text_by_id["start-button"].strip(),
            "开始一个事项",
        )

        buttons = self.page.attrs_for("button", id="start-button")
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0].get("type"), "button")

        statuses = self.page.attrs_for("p", id="start-status")
        self.assertEqual(len(statuses), 1)
        self.assertEqual(statuses[0].get("role"), "status")
        self.assertEqual(statuses[0].get("aria-live"), "polite")

    def test_inline_css_and_javascript_wire_the_required_interaction(self):
        self.assertTrue(self.page.style_text.strip(), "CSS must be inline")
        self.assertTrue(self.page.script_text.strip(), "JavaScript must be inline")

        script = self.page.script_text
        self.assertIn("getElementById('start-button')", script)
        self.assertIn("getElementById('start-status')", script)
        self.assertIn("addEventListener('click'", script)
        self.assertIn("startStatus.textContent = '事项工作区已准备好'", script)
        self.assertIn("startButton.disabled = true", script)

    def test_page_is_self_contained_without_external_resources(self):
        self.assertNotRegex(self.source, r"https?://")
        self.assertEqual(self.page.attrs_for("link"), [])
        self.assertFalse(
            any("src" in attrs for _tag, attrs in self.page.tags),
            "A single-file page must not load external src resources",
        )
        for tag, attrs in self.page.tags:
            if "href" in attrs:
                self.assertTrue(
                    attrs["href"].startswith("#"),
                    f"Unexpected non-anchor href on <{tag}>",
                )

        inline_content = f"{self.page.style_text}\n{self.page.script_text}".lower()
        for marker in ("@import", "url(http://", "url(https://", "url(//"):
            self.assertNotIn(marker, inline_content)

    def test_semantic_structure_and_basic_keyboard_accessibility(self):
        tag_names = {tag for tag, _attrs in self.page.tags}
        for required in ("header", "main", "footer", "article"):
            self.assertIn(required, tag_names)

        self.assertTrue(
            any(
                attrs.get("href") == "#main-content"
                for _tag, attrs in self.page.tags
            ),
            "Expected a skip link to the main content",
        )
        self.assertIn(":focus-visible", self.page.style_text)


if __name__ == "__main__":
    unittest.main()
