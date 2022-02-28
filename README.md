# BioPortal-to-KGX

Assemble a BioPortal Knowledge Graph through the following steps:

* Transform the BioPortal 4store data dump to KGX graphs, with ROBOT preprocessing
* Validate the output graphs with KGX to determine alignment to the Biolink Model
* Obtain additional ontology metadata through the Bioportal API
* Retrieve mappings for nodes without clear Bioportal analogues through Bioportal

## Usage

Prepare a dump of the Bioportal 4store data with the `4s-dump` script.

The dump will be in the form of n-triples, with individual sets of records in nested directories and one line of metadata at the top of each file.

Run BioPortal-to-KGX as:

```
python run.py --input ../path/to/your/data/ --kgx_validate
```

Leave off the `--kgx_validate` flag to skip validation, which can be time-consuming and may not be appropriate for your data.

Output will be written to the `/4store-to-kgx` directory within `/transformed`, with subdirectories named for the 4store graph and each subgraph.
Each subgraph will contain node and edge files ({subgraph_name}_nodes.tsv and {subgraph_name}_edges.tsv, respectively) along with logs containing any validation messages about the transforms.
