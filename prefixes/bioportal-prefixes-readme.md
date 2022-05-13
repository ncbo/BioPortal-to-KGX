# BioPortal Prefixes

Prefixes used across IRIs within BioPortal ontologies are identified within two files:

* Automated inferred prefixes are in `bioportal-prefixes.tsv`.
* Manually-curated prefixes are in `bioportal-prefixes-curated.tsv`

Both files contain the following columns:

* ontology - The name of the ontology using the prefix
* prefix  - The string of the prefix (e.g., 'http://childhealthservicemodels.eu/asthma')
* delimiter - The delimiter separating the prefix from the class ID (e.g, '#')
* native - True if the prefix refers to classes of the ontology itself, False if it is from a imported/referenced ontology, or otherwise Unknown.
            One ontology may have *more than one* native prefix.

Manually-curated prefixes are primarily native, rather than the set of all prefixes used within each ontology.
Some non-native prefixes are included.