# RDF Graph Operations Library

This library provides tools for interacting with RDF graphs via a SPARQL endpoint.
It includes functions to find the `Lowest Common Ancestor` (LCA) of a set of classes and to populate an RDF graph with triples related to a given parent node.

## Installation

Ensure you have Python installed on your system.

Install the SOFT7 package with the `graph` extra:

```bash
pip install soft7[graph}
```

## Functions

### 1. find_parent_node

This function queries a SPARQL endpoint to find the Lowest Common Ancestor (LCA) of a list of class URIs within a specified graph URI.

#### Parameters

* **sparql (`SPARQLWrapper`)**: An instance of SPARQLWrapper configured for the target SPARQL service.
* **class_names (`list[str]`)**: The class URIs to find a common parent for.
* **graph_uri (`str`)**: The URI of the graph in which to perform the query.

#### Returns

* **str | None**: The URI of the common parent node if one exists, otherwise `None`.

#### Raises

* **SPARQLWrapperException**: If there is an error in executing or processing the SPARQL query.
* **TemplateError**: If there is an error in rendering the SPARQL query using Jinja2 templates.

#### Usage Example

```python
...
sparqlWrapper = SPARQLWrapper(sparql_endpoint)
sparqlWrapper.setHTTPAuth(BASIC)
sparqlWrapper.setCredentials(username, password)

parent_node = find_parent_node(
    sparql=sparqlWrapper,  
    class_names=["http://example.com/class1", "http://example.com/class2"],
    graph_uri="http://example.com/graph"
)
```

### 2. fetch_and_populate_graph

Fetches and populates an RDF graph with triples related to a specified parent node.

#### Parameters

* **sparql (`SPARQLWrapper`)**: An instance of SPARQLWrapper configured for the target SPARQL service.
* **graph_uri (`str`)**: The URI of the graph from which triples will be fetched.
* **parent_node (`str`)**: The URI of the parent node to base the triple fetching on.
* **graph (`rdflib.Graph`, `optional`)**: An instance of an RDFlib graph to populate with fetched triples.
  If `None`, a new empty graph is created. Defaults to `None`.

#### Returns

* **rdflib.Graph**: The graph populated with the fetched triples.

#### Raises

* **SPARQLWrapperException**: If there is an error in executing or processing the SPARQL query.
* **RDFLibException**: If there is an error in adding fetched triples to the RDF graph.

#### Usage Example

```python
...

rdf_graph = fetch_and_populate_graph(
    sparql=sparqlWrapper,
    graph_uri="http://example.com/graph",
    parent_node="http://example.com/parentClass"
)
```

### Error Handling

Both functions handle errors internally and will return `None` if an error occurs during execution.
Errors during SPARQL querying or RDF graph manipulation are logged to the console.
