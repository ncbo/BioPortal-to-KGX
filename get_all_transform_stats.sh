#!/bin/bash
# Get all transformation stats for BioPortal ontologies
#

TX_PATH="./transformed/ontologies/"

# KGX validation error types
all_errortypes=("MISSING_NODE_PROPERTY"
 "MISSING_EDGE_PROPERTY"
 "INVALID_NODE_PROPERTY"
 "INVALID_EDGE_PROPERTY"
 "INVALID_NODE_PROPERTY_VALUE_TYPE"
 "INVALID_NODE_PROPERTY_VALUE"
 "INVALID_EDGE_PROPERTY_VALUE_TYPE"
 "INVALID_EDGE_PROPERTY_VALUE"
 "MISSING_CATEGORY"
 "INVALID_CATEGORY"
 "Category 'OntologyClass' is a mixin in the Biolink Model"
 "MISSING_EDGE_PREDICATE"
 "INVALID_EDGE_PREDICATE"
 "MISSING_NODE_CURIE_PREFIX"
 "DUPLICATE_NODE"
 "MISSING_NODE"
 "INVALID_EDGE_TRIPLE"
 "VALIDATION_SYSTEM_ERROR"
)

# Run
echo "All processed ontologies:"
ls -d transformed/ontologies/* | wc -l

echo "All successful JSON transforms:"
find $TX_PATH -name "*.json" | wc -l

echo "All successful KGX TSV transforms:"
find $TX_PATH -name "*_edges.tsv" | wc -l

echo "Transforms with at least one of the following errors:"
for ((i=0; i < ${#all_errortypes[@]}; i++))
do
    echo "${all_errortypes[$i]}"
    grep -r -m1 --include \*.log "${all_errortypes[$i]}" $TX_PATH | wc -l
done

echo "Complete."
