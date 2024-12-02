"""Unit tests for the graph module"""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pytest


class TestFindParentNode(unittest.TestCase):
    """Testclass"""

    @patch("s7.graph.utils.SPARQLWrapper")
    def test_find_parent_node_success(self, mock_wrapper):
        """Set up the mock for successful return"""
        from s7.graph.utils import find_parent_node

        sparql = mock_wrapper.return_value
        sparql.query().convert.return_value = {
            "results": {
                "bindings": [{"parentClass": {"value": "http://example.com/Parent"}}]
            }
        }

        # Assuming class_names list and graph_uri are provided correctly
        result = find_parent_node(
            sparql, ["http://example.com/Class1"], "http://example.com/graph"
        )

        assert result == "http://example.com/Parent"

    @patch("s7.graph.utils.SPARQLWrapper")
    def test_find_parent_node_no_parent_found(self, mock_wrapper):
        """Set up the mock for no parent found"""
        from s7.graph.utils import find_parent_node

        sparql = mock_wrapper.return_value
        sparql.query().convert.return_value = {"results": {"bindings": []}}

        result = find_parent_node(
            sparql, ["http://example.com/Class1"], "http://example.com/graph"
        )
        assert result is None

    @patch("s7.graph.utils.SPARQLWrapper")
    def test_find_parent_node_exception(self, mock_wrapper):
        """Simulate a RuntimError exception"""
        from s7.graph.utils import find_parent_node

        sparql = mock_wrapper.return_value
        sparql.query.side_effect = RuntimeError("SPARQL error")

        with pytest.raises(RuntimeError):
            find_parent_node(
                sparql, ["http://example.com/Class1"], "http://example.com/graph"
            )


class TestFetchAndPopulateGraph(unittest.TestCase):
    """Testclass"""

    @patch("s7.graph.utils.SPARQLWrapper")
    @patch("s7.graph.utils.rdflib.Graph")
    def test_fetch_and_populate_graph_success(self, mock_graph, mock_wrapper):
        """Set up mocks"""
        from s7.graph.utils import fetch_and_populate_graph

        sparql = mock_wrapper.return_value
        graph = mock_graph.return_value
        sparql.query().convert.return_value = {
            "results": {
                "bindings": [
                    {
                        "subject": {"value": "sub"},
                        "predicate": {"value": "pred"},
                        "object": {"value": "obj"},
                    }
                ]
            }
        }

        result = fetch_and_populate_graph(
            sparql, "http://example.com/graph", "http://example.com/Parent", graph
        )

        assert graph.add.called
        assert result == graph

    @patch("s7.graph.utils.SPARQLWrapper")
    def test_fetch_and_populate_graph_failure(self, mock_wrapper):
        """Simulate a SPARQLWrapper exception"""
        from s7.graph.utils import fetch_and_populate_graph

        sparql = mock_wrapper.return_value
        sparql.query.side_effect = RuntimeError("SPARQL error")

        with pytest.raises(RuntimeError):
            fetch_and_populate_graph(
                sparql, "http://example.com/graph", "http://example.com/Parent"
            )
