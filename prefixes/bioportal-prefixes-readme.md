# BioPortal Prefixes

Prefixes used across IRIs within BioPortal ontologies are identified within `bioportal-prefixes-curated.tsv`.

This file contains the following columns:

* ontology - The name of the ontology using the prefix
* prefix  - The string of the prefix (e.g., 'http://childhealthservicemodels.eu/asthma')
* delimiter - The delimiter separating the prefix from the class ID (e.g, '#')
* native - True if the prefix refers to classes of the ontology itself, False if it is from a imported/referenced ontology, or otherwise Unknown.

One ontology may have *more than one* native prefix.
Not all ontologies have a native prefix - some are entirely imports.

Manually-curated prefixes are primarily native, rather than the set of all prefixes used within each ontology.
Some non-native prefixes are included.

The file `bioportal-preferred-prefixes` contains mappings from Bioportal ontology names to preferred names. These are used in order to avoid conflicts across ontology sources, e.g., `RO` in OBO Foundry is the Relation Ontology, while in BioPortal `RO` refers to the Radiomics Ontology. To avoid conflict, CURIEs for nodes from the latter are prefixed with BIOPORTAL.RO. The BioPortal name for the Relation Ontology, `OBOREL`, is prefixed as `RO` for greater cross-platform interoperability.
