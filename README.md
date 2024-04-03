# SOFT7

## OTEAPI plugin

The `soft7` packages comes with an [OTEAPI](https://github.com/EMMC-ASBL/oteapi-core) plugin that allows one to convert any core parser data to a SOFT7 Entity instance.

To use the plugin, call the `'soft7'` `functionType` function strategy.

### Test the plugin

At the root of the repository is a [Docker Compose](https://docs.docker.com/compose/) file, which, when run, will start an [OTEAPI Service](https://github.com/EMMC-ASBL/oteapi-services#readme) that includes the `soft7` OTEAPI plugin.

To start the service, run:

```bash
docker compose pull
docker compose up -d
```

To follow along with the installation of the `soft7` package and startup of the OTEAPI Service, run:

```bash
docker logs -f soft7-oteapi-1
```

Press Ctrl+C to stop following the logs.

To eventually stop the services, run:

```bash
docker compose down
```

But first, let's test the plugin.

Open a Python shell, an [IPython shell](https://ipython.org/), or a [Jupyter Notebook](https://jupyter.org/), and run:

```python
from s7.factories import create_datasource

# Let us use an OPTIMADE structure from the Materials Project as our "raw" data source.
# The chosen structure is mp-1228448 (Al2O3):
# https://materialsproject.org/materials/mp-1228448/
# For more information about OPTIMADE, see https://www.optimade.org/
# For more information about the Materials Project, see https://materialsproject.org/
dataresource_config = {
    "downloadUrl": (
        "https://optimade.materialsproject.org/v1/structures/mp-1228448?"
        "response_format=json"
    ),
    "mediaType": "application/json",
}

# We need to setup a mapping configuration to tell the plugin how to map the OPTIMADE
# structure to a SOFT7 Entity instance.
# This requires knowledge of the OPTIMADE structure and the SOFT7 Entity.
# In our case the OPTIMADE structure specification is available at
# https://github.com/Materials-Consortia/OPTIMADE/blob/v1.1.0/optimade.rst#structures-entries
# and the SOFT7 Entity of choice is the `OPTIMADEStructure` Entity, which can be found
# at http://onto-ns.com/meta/1.0/OPTIMADEStructure
mapping_config = {
    "mappingType": "triples",
    "prefixes": {
        "optimade": "https://optimade.materialsproject.org/v1/structures/mp-1228448#",
        "soft7": "http://onto-ns.com/meta/1.0/OPTIMADEStructure#",
    },
    "triples": {
        ("optimade:data.id", "", "soft7:properties.id"),
        ("optimade:data.type", "", "soft7:properties.type"),
        ("optimade:data.attributes", "", "soft7:properties."),
    }
}
```
