# BioPortal-to-KGX

Assemble a BioPortal Knowledge Graph through the following steps:

* Transform the BioPortal 4store data dump to KGX graphs, with ROBOT preprocessing
* Validate the output graphs with KGX to determine alignment to the Biolink Model
* Obtain additional ontology metadata through the Bioportal API
* Retrieve mappings for nodes without clear Bioportal analogues through Bioportal

## Usage

Prepare a dump of the Bioportal 4store data with the `4s-dump` script.

The dump will be in the form of n-triples, with individual sets of records in nested directories and one line of metadata at the top of each file.

Run BioPortal-to-KGX with all validation and metadata retrieval options as:

```
python run.py --input ../path/to/your/data/ --kgx_validate --robot_validate --pandas_validate --get_bioportal_metadata --ncbo_key YOUR_NCBO_API_KEY_HERE
```

Specify individual ontologies to include or exclude with the --include_only and --exclude options, respectively, each followed by a comma-delimited list of the original hashed file ID from the 4store dump. 

For example:
```
python run.py --input ../path/to/your/data/ --include_only dabd4d902360003975fb25ae56f8,7b95f2cc27c8fb0d5df11fbdb078
```

Output will be written to the `/bioportal_to_kgx` directory within `/transformed`, with subdirectories named for the 4store graph and each subgraph.

Each subgraph will contain node and edge files ({subgraph_name}_nodes.tsv and {subgraph_name}_edges.tsv, respectively) along with logs containing any validation messages about the transforms.
