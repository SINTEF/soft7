from jinja2 import Template
import uuid

__ttl_template__ = """
@prefix : <{{ base }}#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix soft: <http://www.quaat.com/ontologies#> .
@base <{{ base }}> .

{% set entity_uuid = uuid() %}
{% set uri_uuid = uuid() %}
:Entity_{{ entity_uuid }} rdf:type owl:NamedIndividual ,
                                             soft:Entity ;
                                             soft:uri "{{ dict['uri'] }}"^^xsd:anyURI ;
                                             rdfs:label "{{ name }}"@en .


#################################################################
#    Dimensions
#################################################################
{% set dim_uuid = {} %}
{% for dimension in dict['dimensions'] %}
{% set _dummy = dim_uuid.update( {dimension: uuid() }) %}
:Dimension_{{ dim_uuid[dimension] }} rdf:type owl:NamedIndividual ,
                                             soft:Dimension ;
                                             :dp_dimension_id "{{ dimension }}"^^xsd:string ,
                                             "{{ dict['dimensions'][dimension] }}"^^xsd:string ;
                                             rdfs:label "{{ dimension }}"@en .

:Entity_{{ entity_uuid }} soft:dimension :Dimension_{{ dim_uuid[dimension] }} .
                                         
{% endfor %}


#################################################################
#    Properties
#################################################################

{% set prop_uuid = {} %}
{% for property in dict['properties'] %}
{% set _dummy = prop_uuid.update( {property: uuid() }) %}
{% if 'shape' in dict['properties'][property] %}
####################
#    Property shapes
####################

{% set shape_uuid = {} %}    
{% for idx, shape in enumerate(dict['properties'][property]['shape']) | reverse %}

{% set _dummy = shape_uuid.update( {shape: uuid() }) %}        
:Shape_{{ shape_uuid[shape]}} rdf:type owl:NamedIndividual ,
                                             soft:Shape ;
                                             soft:hasDimension :Dimension_{{dim_uuid[shape]}} ;
{% if idx < (len(dict['properties'][property]['shape']) - 1) %}
                                             soft:hasShape :Shape{{ shape_uuid[(dict['properties'][property]['shape'][idx+1])] }} ;{% endif %}
                                             rdfs:label "{{ shape }}"@en .
{% endfor %}

{% endif %}

############## Property: {{ property }}

:Property_{{ prop_uuid[property] }} rdf:type owl:NamedIndividual ,
                                             soft:Property ;
{% if 'shape' in dict['properties'][property] %}
                                             soft:hasShape :Shape_{{shape_uuid[(dict['properties'][property]['shape'][0])]}} ;
{% endif %}                                             
                                             soft:property_description "{{ dict['properties'][property]['description'] }}"^^xsd:string ;
                                             soft:property_label "{{ dict['properties'][property]['label'] }}"^^xsd:string ;
                                             soft:property_type "{{ dict['properties'][property]['type'] }}"^^xsd:string ;
                                             soft:property_unit "{{ dict['properties'][property]['unit'] }}"^^xsd:string ;
                                             rdfs:label "{{ property }}"@en .

:Entity_{{ entity_uuid }} soft:property :Property_{{ prop_uuid[property] }} .
{% endfor %}

"""


class Turtle:
    """
    Turtle RDF format writer
    """
    
    @staticmethod
    def dumps(dict):
        """
        """        
        template = Template(__ttl_template__)
        output = template.render(base="http://example.com/entity", 
                                 name='Entity', 
                                 len=len, 
                                 enumerate=enumerate, 
                                 dict=dict, 
                                 uuid=lambda : str(uuid.uuid4()).replace('-','_'))
        return output
    
    
    @staticmethod
    def dump(dict, file):
        """
        """
        with open (file, "w") as ttl:
            ttl.write(dumps(dict))