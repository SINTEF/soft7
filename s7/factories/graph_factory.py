"""Generate SOFT7 (outer mapping) entities based on basic information:

1. SOFT7 entity data model.
2. Semantic Mapping.
3. Internal data source SOFT7 entity.

"""
from enum import Enum
from pathlib import Path
from types import FunctionType
from typing import Any, Callable, Iterable, Optional, Type, Union

import yaml

# from IPython import display
from oteapi.models import ResourceConfig
from pydantic import Field, create_model

from s7.graph import Graph
from s7.pydantic_models.soft7 import SOFT7DataEntity, SOFT7Entity

TEST_KNOWLEDGE_BASE = Graph(
    [
        ("imp_to_eis", "isA", "function"),
        ("imp_to_eis", "expects", "ImpedancekOhmCm2"),
        ("imp_to_eis", "outputs", "EISEfficiency"),
        ("imp_to_lpr", "isA", "function"),
        ("imp_to_lpr", "expects", "LPR24h"),
        ("imp_to_lpr", "outputs", "LPREfficiency"),
        ("imp_pow_func", "isA", "function"),
        ("imp_pow_func", "expects", "ImpedanceLogOhm"),
        ("imp_pow_func", "outputs", "ImpedanceOhm"),
        ("impkflux", "isA", "function"),
        ("impkflux", "expects", "ImpedanceOhm"),
        ("impkflux", "outputs", "ImpedancekOhmCm2"),
        ("cas_to_smiles", "isA", "function"),
        ("cas_to_smiles", "expects", "CASNumber"),
        ("cas_to_smiles", "outputs", "SMILES"),
        ("cas_to_inchi", "isA", "function"),
        ("cas_to_inchi", "expects", "CASNumber"),
        ("cas_to_inchi", "outputs", "InChI"),
        # ("cas_to_cas", "isA", "function"),
        # ("cas_to_cas", "expects", "CASNumber"),
        # ("cas_to_cas", "outputs", "CASNumber"),
        ("LPR24h", "isA", "Resistance"),
        ("ImpedanceOhm", "isA", "Resistance"),
        ("ImpedanceLogOhm", "isA", "Resistance"),
        ("ImpedancekOhmCm2", "isA", "Resistance"),
        ("EISEfficiency", "isA", "InhibitorEfficiency"),
        ("LPREfficiency", "isA", "InhibitorEfficiency"),
        ("PDPEfficiency", "isA", "InhibitorEfficiency"),
        ("Resistance", "isA", "Parameter"),
        ("InhibitorEfficiency", "isA", "Output"),
    ]
)


class HashableResourceConfig(ResourceConfig):
    """ResourceConfig, but hashable."""

    def __hash__(self) -> int:
        return hash(
            tuple(
                (field_name, field_value)
                if isinstance(field_value, (str, bytes, tuple, frozenset, int, float))
                or field_value is None
                else (field_name, None)
                for field_name, field_value in self.__dict__.items()
            )
        )


class SOFT7EntityPropertyType(str, Enum):
    """Property type enumeration."""

    STR = "string"
    FLOAT = "float"

    @property
    def py_cls(self) -> type:
        """Get the equivalent Python cls."""
        return {
            self.STR: str,
            self.FLOAT: float,
        }[self]


def _get_inputs(
    name: str, graph: Graph
) -> list[tuple[str, Optional[FunctionType], Optional[tuple[str, ...]]]]:
    """Retrieve all inputs/parameters for a function ONLY if it comes from internal
    entity."""
    expects = [expect for _, _, expect in graph.match(name, "expects", None)]
    # print(expects)

    inputs: list[str] = []
    for expect in expects:
        mapped_input = [input_ for input_, _, _ in graph.match(None, "mapsTo", expect)]
        if len(mapped_input) > 1:
            raise RuntimeError(
                f"Expected exactly 1 mapping to {expect}, instead found "
                f"{len(mapped_input)} !"
            )
        inputs.extend(mapped_input)
    # print(inputs)
    if not inputs:
        return [(_, None, None) for _ in expects]

    input_getters = []
    for input_ in inputs:
        mapped_getter = [
            function_ for _, _, function_ in graph.match(input_, "get", None)
        ]
        if len(mapped_getter) > 1:
            raise RuntimeError(
                f"Expected exactly 1 getter function for {input_!r}, instead found "
                f"{len(mapped_getter)} !"
            )
        input_getters.append(mapped_getter[0])

    return list(
        zip(
            expects,
            input_getters,
            [tuple(input_.split(".")) for input_ in inputs],
        )
    )


def _get_property_local(
    graph: Graph,
    inner_entities: dict[str, SOFT7DataEntity],
) -> Callable[[str], Any]:
    """Get a property - local."""
    predicate_filter = ["mapsTo", "outputs", "expects", "hasProperty", "hasPart"]
    node_filter = ["outer"]

    def __get_property(name: str) -> Any:
        paths = graph.path(f"outer.{name}", "inner_data", predicate_filter, node_filter)
        print(paths)
        for path in paths:
            if len([_ for _ in path if "." in _]) == 2:
                break
        else:
            raise RuntimeError("Could not determine a proper path through the graph !")
        print("Graph traversed! Path:", " -> ".join(path))
        # if len(path) > 1:
        #     raise RuntimeError("Found more than one path through the graph !")
        # path = path[0]

        functions = [
            _
            for _ in path
            if _ in [s for s, _, _ in graph.match(None, "isA", "function")]
        ]
        # print(functions)

        if not functions:
            raise RuntimeError(
                f"No function found to retrieve {name!r} - what a stupid path"
            )

        functions_dict: dict[str, dict[str, Any]] = {}
        for function_name in functions:
            functions_dict[function_name] = {
                "inputs": _get_inputs(function_name, graph),
                "function": [
                    function_
                    for _, _, function_ in graph.match(function_name, "executes", None)
                ][0],
            }

        res = None
        for function_name in reversed(functions):
            if functions_dict[function_name]["inputs"][0][-1]:
                res = functions_dict[function_name]["function"](
                    **{
                        param_name: getter_func(
                            inner_entities[getter_func_param[0]], getter_func_param[1]
                        )
                        for (
                            param_name,
                            getter_func,
                            getter_func_param,
                        ) in functions_dict[function_name]["inputs"]
                    }
                )
            else:
                res = functions_dict[function_name]["function"](
                    **{
                        param_name: res
                        for param_name, _, _ in functions_dict[function_name]["inputs"]
                    }
                )

        return res

    return __get_property


def create_outer_entity(
    data_model: Union[SOFT7Entity, Path, str, dict[str, Any]],
    inner_entities: dict[str, SOFT7DataEntity],
    mapping: Union[Graph, Iterable[tuple[str, str, str]]],
) -> Type[SOFT7DataEntity]:
    """Create and return a SOFT7 entity wrapped as a pydantic model.

    Parameters:
        data_model: A SOFT7 data model entity or a string/path to a YAML file of the
            data model.
        inner_entity: The data source SOFT7 entity.
        mapping: A sequence of RDF triples representing the mapping.

    Returns:
        A SOFT7 entity class wrapped as a pydantic data model.

    """
    if isinstance(data_model, (str, Path)):
        if not Path(data_model).resolve().exists():
            raise FileNotFoundError(
                f"Could not find a data model YAML file at {data_model!r}"
            )
        data_model: dict[str, Any] = yaml.safe_load(  # type: ignore[no-redef]
            Path(data_model).resolve().read_text(encoding="utf8")
        )
    if isinstance(data_model, dict):
        data_model = SOFT7Entity(**data_model)
    if not isinstance(data_model, SOFT7Entity):
        raise TypeError("data_model must be a 'SOFT7Entity'")

    if not isinstance(inner_entities, dict) or not all(
        isinstance(entity, SOFT7DataEntity) for entity in inner_entities.values()
    ):
        raise TypeError("inner_entity must be a dict with SOFT7DataEntity as values")

    if isinstance(mapping, Iterable):
        mapping = Graph(list(mapping))
    if not isinstance(mapping, Graph):
        raise TypeError("mapping must be a Graph")

    if any(property_name.startswith("_") for property_name in data_model.properties):
        raise ValueError(
            "data model property names may not start with an underscore (_)"
        )

    # Create "complete" local graph
    local_graph = Graph(
        [
            # ("inner", "isA", "DataSourceEntity"),
            ("outer", "isA", "OuterEntity"),
            ("DataSourceEntity", "isA", "SOFT7DataEntity"),
            ("OuterEntity", "isA", "SOFT7DataEntity"),
        ]
    )
    for inner in inner_entities:
        local_graph.append((inner, "isA", "DataSourceEntity"))
        local_graph.append(("inner_data", "hasPart", inner))

    for s, p, o in mapping.triples:
        local_graph.append((s, p, o))
        if not isinstance(s, str):
            continue
        split_subject = s.split(".")
        for triple in [
            (split_subject[0], "hasProperty", s),
            (s, "get", getattr),
        ]:
            local_graph.append(triple)

    for triple in TEST_KNOWLEDGE_BASE.triples:
        local_graph.append(triple)

    # Generate (local) execution relations for functions

    # TODO: Replace LOCAL FUNCTIONS with named entry points
    #    for function_name, _, _ in local_graph.match(p="isA", o="function"):
    #        missing_functions = []
    #        if not hasattr(known_functions, function_name):
    #            missing_functions.append(function_name)
    #        else:
    #            local_graph.append(
    #                (
    #                    function_name,
    #                    "executes",
    #                    getattr(known_functions, function_name),
    #                )
    #            )
    #        if missing_functions:
    #            raise ValueError(
    #                f"{missing_functions} not found in known (local) functions !"
    #            )

    return create_model(  # type: ignore[call-overload]
        __model_name="OuterEntity",
        __config__=None,
        __base__=SOFT7DataEntity,
        __module__=__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **{
            property_name: Field(  # type: ignore[pydantic-field]
                default_factory=lambda: _get_property_local(
                    local_graph, inner_entities
                ),
                description=property_value.description,
                title=property_name.replace(" ", "_"),
                type=property_value.type_.py_cls,
                **{
                    f"x-{field}": getattr(property_value, field)
                    for field in property_value.__fields__
                    if field not in ("description", "type_", "shape")
                    and getattr(property_value, field)
                },
            )
            for property_name, property_value in data_model.properties.items()
        },
    )
