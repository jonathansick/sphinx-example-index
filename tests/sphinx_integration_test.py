# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Tests that use the Sphinx pytest fixture to build a test case site and
permit inspection of the Sphinx application object.
"""

import os
from typing import TYPE_CHECKING

import pytest
from sphinx.util import logging
from bs4 import BeautifulSoup

from tests.utils import is_directive_registered, is_node_registered

from sphinx_example_index.pages import ExamplePage, Renderer, TagPage
from sphinx_example_index.marker import ExampleMarkerNode, EXAMPLE_SRC_DIV_CLASS
from sphinx_example_index.preprocessor import detect_examples

if TYPE_CHECKING:
    from io import StringIO
    from sphinx.application import Sphinx


@pytest.mark.sphinx("html", testroot="example-index")
def test_setup(app: "Sphinx", status: "StringIO", warning: "StringIO") -> None:
    """Test that sphinx_example_index is set up by Sphinx and that all its
    features are added.
    """
    assert "sphinx_example_index" in app.extensions

    # Check registered directives
    assert is_directive_registered("example")

    # Check registered configs
    assert "example_index_dir" in app.config  # type: ignore
    assert "example_index_enabled" in app.config  # type: ignore
    assert "example_index_h1" in app.config  # type: ignore

    # Check registered nodes
    assert is_node_registered(ExampleMarkerNode)


@pytest.mark.sphinx("html", testroot="example-index")
def test_example_directive_targets(
    app: "Sphinx", status: "StringIO", warning: "StringIO"
) -> None:
    """Test that the example directive creates target nodes with the
    appropriate Ids.
    """
    app.verbosity = 2
    logging.setup(app, status, warning)
    app.builder.build_all()

    with open(os.path.join(app.outdir, "page-with-examples.html")) as f:
        soup = BeautifulSoup(f, "html.parser")

    known_target_refids = [
        "example-src-example-with-two-paragraphs",
        "example-src-tagged-example",
        "example-src-example-with-multiple-tags",
        "example-src-example-with-subsections",
    ]
    for known_target_refid in known_target_refids:
        divs = soup.find_all("div", id=known_target_refid)
        assert len(divs)
        assert EXAMPLE_SRC_DIV_CLASS in divs[0]["class"]


@pytest.mark.sphinx("dummy", testroot="example-index")
def test_detect_examples(
    app: "Sphinx", status: "StringIO", warning: "StringIO"
) -> None:
    """Test that the detect_examples function can match "example"
    directives using the "page-with-examples.rst" test case.
    """
    test_filepath = os.path.join(app.srcdir, "page-with-examples.rst")
    examples = list(detect_examples(test_filepath, app.env))

    assert examples[0].title == "Example with two paragraphs"
    assert examples[0].tags == set()
    assert examples[0].docname == "page-with-examples"
    assert examples[0].docref == "/page-with-examples"

    assert examples[1].title == "Tagged example"
    assert examples[1].tags == set(["tag-a"])
    assert repr(examples[1]) == (
        "ExampleSource('Tagged example', 'page-with-examples', tags={'tag-a'})"
    )
    assert examples[1].docname == "page-with-examples"
    assert examples[1].docref == "/page-with-examples"

    assert examples[2].title == "Example with multiple tags"
    assert examples[2].tags == set(["tag-a", "tag-b"])
    assert examples[2].docname == "page-with-examples"
    assert examples[2].docref == "/page-with-examples"

    assert examples[3].title == "Example with subsections"
    assert examples[3].tags == set(["tag-b"])
    assert examples[3].docname == "page-with-examples"
    assert examples[3].docref == "/page-with-examples"

    # Test comparisons (by title)
    assert examples[0] < examples[1]
    assert examples[0] <= examples[1]
    assert examples[1] > examples[0]
    assert examples[1] >= examples[0]
    assert examples[1] != examples[0]
    assert examples[0] == examples[0]


@pytest.mark.sphinx("dummy", testroot="example-index")
def test_example_page(
    app: "Sphinx", status: "StringIO", warning: "StringIO"
) -> None:
    """Test ExamplePage and Renderer using examples from the
    "page-with-examples.rst" test case.

    This test avoids the complete preprocessing pipeline and just tests the
    template rendering step.
    """
    env = app.env
    renderer = Renderer(builder=app.builder, h1_underline="#")

    # Test using example-with-two-paragraphs
    test_filepath = os.path.join(app.srcdir, "page-with-examples.rst")
    examples = list(detect_examples(test_filepath, env))
    example = examples[0]

    examples_dir = os.path.join(
        app.srcdir, app.config.example_index_dir  # type: ignore
    )
    example_page = ExamplePage(
        source=example, examples_dir=examples_dir, app=app
    )

    assert example_page.source == example
    assert example_page.rel_docref == "example-with-two-paragraphs"
    assert example_page.docref == "/examples/example-with-two-paragraphs"
    assert example_page.filepath.endswith(example_page.docref + ".rst")

    rendered_page = example_page.render(renderer)
    expected = (
        "Example with two paragraphs\n"
        "###########################\n"
        "\n"
        "From :doc:`/page-with-examples`.\n"
    )
    assert rendered_page == expected


@pytest.mark.sphinx("dummy", testroot="example-index")
def test_example_page_tagged(
    app: "Sphinx", status: "StringIO", warning: "StringIO"
) -> None:
    """Test ExamplePage and Renderer using a tagged example from the
    ``page-with-examples.rst`` test case.
    """
    env = app.env
    renderer = Renderer(builder=app.builder, h1_underline="#")

    # Test using example-with-multiple-tags
    test_filepath = os.path.join(app.srcdir, "page-with-examples.rst")
    examples = list(detect_examples(test_filepath, env))
    example = examples[2]

    examples_dir = os.path.join(
        app.srcdir, app.config.example_index_dir  # type: ignore
    )
    example_page = ExamplePage(
        source=example, examples_dir=examples_dir, app=app
    )
    # Generate a tag page to associate with the example page
    for tag_page in TagPage.generate_tag_pages(
        example_pages=[example_page], examples_dir=examples_dir, app=app
    ):
        tag_page.render_and_save(renderer)

    assert example_page.source == example
    assert example_page.rel_docref == "example-with-multiple-tags"
    assert example_page.docref == "/examples/example-with-multiple-tags"

    rendered_page = example_page.render(renderer)
    expected = (
        "Example with multiple tags\n"
        "##########################\n"
        "\n"
        "From :doc:`/page-with-examples`.\n"
        "\n"
        "Tagged:\n"
        ":doc:`tag-a </examples/tags/tag-a>`,\n"
        ":doc:`tag-b </examples/tags/tag-b>`."
    )
    assert rendered_page == expected


@pytest.mark.sphinx("dummy", testroot="custom-template")
def test_example_page_custom_template(
    app: "Sphinx", status: "StringIO", warning: "StringIO"
) -> None:
    """Test ExamplePage and Renderer using examples from the
    "page-with-examples.rst" test case for the "custom-template" test case.

    This demonstrates that user templates, configured via the
    ``templates_path`` configuration variable, override the built-in templates.
    """
    env = app.env
    renderer = Renderer(builder=app.builder, h1_underline="#")

    test_filepath = os.path.join(app.srcdir, "page-with-examples.rst")
    examples = list(detect_examples(test_filepath, env))
    example = examples[0]

    examples_dir = os.path.join(
        app.srcdir, app.config.example_index_dir  # type: ignore
    )
    example_page = ExamplePage(
        source=example, examples_dir=examples_dir, app=app
    )

    rendered_page = example_page.render(renderer)
    expected = (
        "Example title\n"
        "#############\n"
        "\n"
        "From :doc:`/page-with-examples`.\n"
        "\n"
        "Custom template!"
    )
    assert rendered_page == expected


@pytest.mark.sphinx("dummy", testroot="example-index")
def test_preprocessor(
    app: "Sphinx", status: "StringIO", warning: "StringIO"
) -> None:
    """Test that the preprocessor builds all of the expected standalone
    example pages.

    This test uses the "example-index" test case.
    """
    examples_source_dir = os.path.join(
        app.srcdir, app.config.example_index_dir  # type: ignore
    )

    # Ensure example pages are written
    example_page_names = [
        "example-with-two-paragraphs.rst",
        "tagged-example.rst",
        "example-with-multiple-tags.rst",
        "example-with-subsections.rst",
    ]
    example_page_paths = [
        os.path.join(examples_source_dir, p) for p in example_page_names
    ]
    for path in example_page_paths:
        assert os.path.exists(path)

    # Ensure tag pages are written
    tag_names = ["tag-a.rst", "tag-b.rst"]
    tag_page_paths = [
        os.path.join(examples_source_dir, "tags", n) for n in tag_names
    ]
    for path in tag_page_paths:
        assert os.path.exists(path)

    # Ensure the index page is written
    index_path = os.path.join(examples_source_dir, "index.rst")
    assert os.path.exists(index_path)
