""" Unit tests for the graph module
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from graph.utils import fetch_and_populate_graph, find_parent_node


class TestFindParentNode(unittest.TestCase):
    """Testclass"""

    @patch("graph.utils.SPARQLWrapper")
    def test_find_parent_node_success(self, mock_wrapper):
        """Set up the mock for successful return"""
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

        self.assertEqual(result, "http://example.com/Parent")

    @patch("graph.utils.SPARQLWrapper")
    def test_find_parent_node_no_parent_found(self, mock_wrapper):
        """Set up the mock for no parent found"""
        sparql = mock_wrapper.return_value
        sparql.query().convert.return_value = {"results": {"bindings": []}}

        result = find_parent_node(
            sparql, ["http://example.com/Class1"], "http://example.com/graph"
        )
        self.assertIsNone(result)

    @patch("graph.utils.SPARQLWrapper")
    def test_find_parent_node_exception(self, mock_wrapper):
        """Simulate a RuntimError exception"""
        sparql = mock_wrapper.return_value
        sparql.query.side_effect = RuntimeError("SPARQL error")

        with self.assertRaises(RuntimeError):
            find_parent_node(
                sparql, ["http://example.com/Class1"], "http://example.com/graph"
            )


class TestFetchAndPopulateGraph(unittest.TestCase):
    """Testclass"""

    @patch("graph.utils.SPARQLWrapper")
    @patch("graph.utils.rdflib.Graph")
    def test_fetch_and_populate_graph_success(self, mock_graph, mock_wrapper):
        """Set up mocks"""
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

        self.assertTrue(graph.add.called)
        self.assertEqual(result, graph)

    @patch("graph.utils.SPARQLWrapper")
    def test_fetch_and_populate_graph_failure(self, mock_wrapper):
        """Simulate a SPARQLWrapper exception"""
        sparql = mock_wrapper.return_value
        sparql.query.side_effect = RuntimeError("SPARQL error")

        with self.assertRaises(RuntimeError):
            fetch_and_populate_graph(
                sparql, "http://example.com/graph", "http://example.com/Parent"
            )


# Running the tests
if __name__ == "__main__":
    unittest.main()
