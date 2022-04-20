#!/bin/bash
# Get counts of UMLS semantic type and concept mappings
# in Bioportal transforms 
#

TX_PATH="./transformed/ontologies/"

STY_PREFIX="http://purl.bioontology.org/ontology/STY/"

# Run
echo "*** Ontologies with edges involving UMLS semantic types:"
grep -r -m1 --include \*_edges.tsv $STY_PREFIX $TX_PATH | awk -F/ '{print $4}'

echo "*** Ontologies with nodes involving UMLS semantic types:"
grep -r -m1 --include \*_nodes.tsv $STY_PREFIX $TX_PATH | awk -F/ '{print $4}'

echo "*** The following codes are used, followed by their usage (combined nodes+edges):"
grep -roh --include \*.tsv "$STY_PREFIX...." $TX_PATH | sort | uniq -c | sort -rn

echo "Complete."
