"""
This library provides tools for interacting with RDF graphs via a
SPARQL endpoint. It includes functions to find the `Lowest Common
Ancestor` (LCA) of a set of classes and to populate an RDF graph with
triples related to a given parent node. The SPARQLWrapper library is
used to handle SPARQL queries and RDFlib for graph operations.

- SemanticMatter 2024
"""

from __future__ import annotations

import logging
from typing import Optional

import rdflib
from jinja2 import Template, TemplateError
from rdflib.exceptions import Error as RDFLibException
from SPARQLWrapper import JSON, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

LOGGER = logging.getLogger(__name__)


def find_parent_node(
    sparql: SPARQLWrapper,
    class_names: list[str],
    graph_uri: str,
) -> str | None:
    """
    Queries a SPARQL endpoint to find a common parent node (LCA) for a given list of
    class URIs within a specified RDF graph.

    Args:
        sparql (SPARQLWrapper): An instance of SPARQLWrapper configured for the target
            SPARQL service.
        class_names (list[str]): The class URIs to find a common parent for.
        graph_uri (str): The URI of the graph in which to perform the query.

    Returns:
        str | None: The URI of the common parent node if one exists, otherwise None.

    Raises:
        RuntimeError: If there is an error in executing or processing the SPARQL query
        or if there is an error in rendering the SPARQL query using Jinja2 templates.

    Note:
        This function assumes that the provided `sparql` instance is already configured
        with necessary authentication and format settings.
    """

    try:
        template_str = """
        {% macro sparql_query(class_names, graph_uri) %}
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?parentClass
        WHERE {
          GRAPH <{{ graph_uri }}> {
            ?class rdfs:subClassOf* ?parentClass .
            FILTER(
                {% for class_name in class_names -%}
                    ?class = <{{ class_name }}>{{ " ||" if not loop.last }}
                {% endfor %})
          }
        }
        {% endmacro %}
        """

        template = Template(template_str)
        query = template.module.sparql_query(class_names, graph_uri)
        LOGGER.debug("Query: %s", query)
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)

        target_count = len(class_names)
        counts: dict[str, int] = {}

        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            parent_class = result["parentClass"]["value"]
            counts[parent_class] = counts.get(parent_class, 0) + 1
            if counts[parent_class] == target_count:
                return parent_class

    except SPARQLWrapperException as wrapper_error:
        raise RuntimeError(
            f"Failed to fetch or parse results: {wrapper_error}"
        ) from wrapper_error

    except TemplateError as template_error:
        raise RuntimeError(
            f"Jinja2 template error: {template_error}"
        ) from template_error

    LOGGER.info("Could not find a common parent node.")
    return None


def fetch_and_populate_graph(
    sparql: SPARQLWrapper,
    graph_uri: str,
    parent_node: str,
    graph: Optional[rdflib.Graph] = None,
) -> rdflib.Graph | None:
    """
    Fetches RDF triples related to a specified parent node from a SPARQL endpoint and
    populates them into an RDF graph.

    Args:
        sparql (SPARQLWrapper): An instance of SPARQLWrapper configured for the target
            SPARQL service.
        graph_uri (str): The URI of the graph from which triples will be fetched.
        parent_node (str): The URI of the parent node to base the triple fetching on.
        graph (rdflib.Graph, optional): An instance of an RDFlib graph to populate with
            fetched triples.
            If `None`, a new empty graph is created. Defaults to `None`.

    Returns:
        Optional[rdflib.Graph]: The graph populated with the fetched triples.

    Raises:
        RuntimeError: If processing the SPARQL query or building the RDF graph fails.

    Note:
        This function assumes that the provided `sparql` instance is already configured
        with necessary authentication and format settings.
    """
    # Create a new graph if one is not provided
    graph = graph or rdflib.Graph()

    try:
        sparql.setReturnFormat(JSON)

        query = f"""
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX fno: <https://w3id.org/function/ontology#>

        SELECT ?subject ?predicate ?object
        WHERE {{
           GRAPH <{graph_uri}> {{
            ?subject ?predicate ?object .
            ?subject rdfs:subClassOf* <{parent_node}> .
            FILTER (?predicate IN (
                rdfs:subClassOf,
                skos:prefLabel,
                rdfs:subPropertyOf,
                rdfs:domain,
                rdfs:range,
                rdf:type,
                owl:propertyDisjointWith,
                fno:expects,
                fno:predicate,
                fno:type,
                fno:returns,
                fno:executes))
           }}
        }}
        """
        LOGGER.debug("Query: %s", query)
        sparql.setQuery(query)

        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            graph.add(
                (
                    rdflib.URIRef(result["subject"]["value"]),
                    rdflib.URIRef(result["predicate"]["value"]),
                    rdflib.URIRef(result["object"]["value"]),
                )
            )

        LOGGER.info("Graph populated with fetched triples.")

    except SPARQLWrapperException as wrapper_error:
        raise RuntimeError(
            f"Failed to fetch or parse results: {wrapper_error}"
        ) from wrapper_error

    except RDFLibException as rdflib_error:
        raise RuntimeError(
            f"Failed to build graph elements: {rdflib_error}"
        ) from rdflib_error

    return graph
