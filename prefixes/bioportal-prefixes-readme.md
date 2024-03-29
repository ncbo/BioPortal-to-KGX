# BioPortal Prefixes

Prefixes used across IRIs within BioPortal ontologies are identified within `bioportal-prefixes-curated.tsv`.

This file contains the following columns:

* ontology - The name of the ontology using the prefix, within BioPortal
* prefix  - The string of the prefix (e.g., 'http://childhealthservicemodels.eu/asthma')
* delimiter - The delimiter separating the prefix from the class ID (e.g, '#')
* native - True if the prefix refers to classes of the ontology itself, False if it is from a imported/referenced ontology, or otherwise Unknown.

One ontology may have *more than one* native prefix.
Not all ontologies have a native prefix - some are entirely imports.

Manually-curated prefixes are primarily native, rather than the set of all prefixes used within each ontology.
Some non-native prefixes are included.
