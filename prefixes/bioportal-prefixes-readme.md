# BioPortal Prefixes

Prefixes used across IRIs within BioPortal ontologies are identified within `bioportal-prefixes.tsv`.

This file contains the following columns:

* ontology - The name of the ontology using the prefix
* prefix  - The string of the prefix (e.g., 'http://childhealthservicemodels.eu/asthma')
* delimiter - The delimiter separating the prefix from the class ID (e.g, '#')
* native - True if the prefix refers to classes of the ontology itself, False if it is from a imported/referenced ontology