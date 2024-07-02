"""This library provides tools for interacting with RDF graphs via a
SPARQL endpoint. It includes functions to find the `Lowest Common
Ancestor` (LCA) of a set of classes and to populate an RDF graph with
triples related to a given parent node. The SPARQLWrapper library is
used to handle SPARQL queries and RDFlib for graph operations.

- SemanticMatter 2024
"""

from __future__ import annotations

import rdflib
from jinja2 import Template, TemplateError
from SPARQLWrapper import BASIC, JSON, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException


def find_parent_node(
    sparql_endpoint: str,
    username: str,
    password: str,
    class_names: list[str],
    graph_uri: str,
) -> str | None:
    """
    Finds the parent node for a list of class names within a specified graph URI.

    Args:
        sparql_endpoint (str): The SPARQL endpoint URL.
        username (str): Username for SPARQL authentication.
        password (str): Password for SPARQL authentication.
        class_names (list[str]): A list of class names to search for parent nodes.
        graph_uri (str): The graph URI to query.

    Returns:
        Optional[str]: The parent node URI if found, else `None`.
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

        sparql = SPARQLWrapper(sparql_endpoint)
        sparql.setHTTPAuth(BASIC)
        sparql.setCredentials(username, password)
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)

        target_count = len(class_names)
        counts = {}

        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            parent_class = result["parentClass"]["value"]
            counts[parent_class] = counts.get(parent_class, 0) + 1
            if counts[parent_class] == target_count:
                return parent_class

    except SPARQLWrapperException as e:
        print(f"Failed to fetch or parse results: {e}", file=sys.stderr)
        return None

    except TemplateError as e:
        print(f"Jinja2 template error: {e}")
        return None

    print("Could not find a common parent node.")
    return None


def fetch_and_populate_graph(
    sparql_endpoint: str, username: str, password: str, graph_uri: str, parent_node: str
) -> rdflib.Graph:
    """
    Fetches and populates an RDF graph with triples related to the given parent node.

    Args:
        sparql_endpoint (str): The SPARQL endpoint URL.
        username (str): Username for SPARQL authentication.
        password (str): Password for SPARQL authentication.
        parent_node (str): The parent node URI to fetch related triples.

    Returns:
        rdflib.Graph: The populated RDF graph, or None if an error occurs.
    """
    g = rdflib.Graph()

    try:
        sparql = SPARQLWrapper(sparql_endpoint)
        sparql.setHTTPAuth(BASIC)
        sparql.setCredentials(username, password)
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
        sparql.setQuery(query)

        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            s = rdflib.URIRef(result["subject"]["value"])
            p = rdflib.URIRef(result["predicate"]["value"])
            o = rdflib.URIRef(result["object"]["value"])
            g.add((s, p, o))

        print("Graph populated with fetched triples.")
    except Exception as e:
        print(f"Failed to fetch or parse results: {e}")
        return None

    return g
