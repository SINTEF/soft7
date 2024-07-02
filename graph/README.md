# RDF Graph Operations Library

This library provides tools for interacting with RDF graphs via a
SPARQL endpoint. It includes functions to find the `Lowest Common
Ancestor` (LCA) of a set of classes and to populate an RDF graph with
triples related to a given parent node.

## Installation
Ensure you have Python installed on your system. You will need the following packages:

* rdflib
* SPARQLWrapper
* jinja2

```bash
	pip install rdflib SPARQLWrapper jinja2
```

## Functions
### 1. find_parent_node
This function queries a SPARQL endpoint to find the Lowest Common Ancestor (LCA) of a list of class URIs within a specified graph URI.

#### Parameters
* **sparql_endpoint (str)**: URL of the SPARQL endpoint.
* **username (str)**: Username for endpoint authentication.
* **password (str)**: Password for endpoint authentication.
* **class_names (list[str])**: URIs of RDF classes to find the LCA for.
* **graph_uri (str)**: URI of the graph where the classes are located.
#### Returns
* str: URI of the LCA if found; otherwise, None.

#### Usage Example
```python
parent_node = find_parent_node(
    sparql_endpoint="http://example.com/sparql",
    username="user",
    password="pass",
    class_names=["http://example.com/class1", "http://example.com/class2"],
    graph_uri="http://example.com/graph"
)
```

### 2. fetch_and_populate_graph
Fetches and populates an RDF graph with triples related to a specified parent node.

#### Parameters
* **sparql_endpoint (str)**: URL of the SPARQL endpoint.
* **username (str)**: Username for endpoint authentication.
* **password (str)**: Password for endpoint authentication.
* **graph_uri (str)**: URI of the graph from which to fetch triples.
* **parent_node (str)**: URI of the parent node to fetch related triples for.
#### Returns
* **rdflib.Graph**: Populated RDF graph; returns None if an error occurs.

#### Usage Example
```python
rdf_graph = fetch_and_populate_graph(
    sparql_endpoint="http://example.com/sparql",
    username="user",
    password="pass",
    graph_uri="http://example.com/graph",
    parent_node="http://example.com/parentClass"
)
```

### Error Handling
Both functions handle errors internally and will return None if an error occurs during execution. Errors during SPARQL querying or RDF graph manipulation are logged to the console.
