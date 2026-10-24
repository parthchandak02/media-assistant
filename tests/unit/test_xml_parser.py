"""Section parsing keeps the headline and subheadline apart."""
from src.utils.xml_parser import match_section_name, parse_xml_sections

SECTIONS = ["headline", "subheadline", "lead", "background"]


def test_subheadline_does_not_overwrite_headline():
    text = (
        "<headline>Main headline</headline>\n"
        '<section name="subheadline">Supporting hook</section>\n'
        '<section name="lead">Opening paragraph</section>\n'
    )
    article, parsed = parse_xml_sections(text, SECTIONS)
    assert article["headline"] == "Main headline"
    assert article["subheadline"] == "Supporting hook"
    assert parsed == ["headline", "subheadline", "lead"]


def test_match_section_name_prefers_exact_then_longest():
    assert match_section_name("subheadline", SECTIONS) == "subheadline"
    assert match_section_name("Sub Headline", ["headline", "sub_headline"]) == "sub_headline"
    assert match_section_name("headline", SECTIONS) == "headline"
    assert match_section_name("background_context", SECTIONS) == "background"
    assert match_section_name("unknown", SECTIONS) is None


def test_spaced_or_hyphenated_subheadline_is_still_subheadline():
    for label in ("Sub Headline", "sub-headline", "SUB_HEADLINE"):
        assert match_section_name(label, SECTIONS) == "subheadline"
