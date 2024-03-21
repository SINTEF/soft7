"""Ontologization of the models.

This module deals with parsing/generating SOFT entities from/to the SOFT entity ontology
(ontology/entity_soft7.ttl).
"""

from __future__ import annotations

from rdflib import DefinedNamespace, Namespace, URIRef


class SOFT(DefinedNamespace):
    """The SOFT7 Entity Ontology (SOFT)"""

    _fail = True
    _NS = Namespace("http://www.quaat.com/ontologies#")

    # http://www.w3.org/2002/07/owl#ObjectProperty
    hasDimension: URIRef
    hasDimensionExpression: URIRef
    hasNextShape: URIRef
    hasProperty: URIRef
    hasShape: URIRef
    hasType: URIRef
    hasUnit: URIRef

    # http://www.w3.org/2002/07/owl#DatatypeProperty
    hasDescription: URIRef
    hasDimensionRef: URIRef
    hasExpressionString: URIRef
    hasLabel: URIRef
    hasURI: URIRef
    hasUnitSymbol: URIRef

    # http://www.w3.org/2002/07/owl#Class
    Blob: URIRef
    Bool: URIRef
    Dimension: URIRef
    DimensionExpression: URIRef
    Entity: URIRef
    Float: URIRef
    Integer: URIRef
    Property: URIRef
    Relation: URIRef
    Shape: URIRef
    String: URIRef
    Type: URIRef
    Unit: URIRef
