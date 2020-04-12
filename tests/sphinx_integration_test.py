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