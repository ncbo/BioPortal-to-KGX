# 4store-to-kgx
Transform a 4store dump to KGX graphs.

## Usage

Prepare a dump of your 4store data with the `4s-dump` script.

The dump will be in the form of n-triples, with individual sets of records in nested directories and one line of metadata at the top of each file.

Run 4store-to-kgx as:
```
python run.py --input ../path/to/your/data/
```

Output will be written to the `/4store-to-kgx` directory within `/transformed`, with subdirectories named for the 4store graph and each subgraph.
Each subgraph will contain node and edge files ({subgraph_name}_nodes.tsv and {subgraph_name}_edges.tsv, respectively) along with logs containing any validation messages about the transforms.
