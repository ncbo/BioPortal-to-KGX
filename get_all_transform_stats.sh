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

all_nodetypes=("biolink:NamedThing"
 "biolink:OntologyClass"
 "biolink:BiologicalProcess"
 "biolink:Cell"
 "biolink:CellularComponent"
 "biolink:ChemicalSubstance"
 "biolink:Disease"
 "biolink:Event"
 "biolink:ExposureEvent"
 "biolink:Gene"
 "biolink:MolecularActivity"
 "biolink:NamedThing"
 "biolink:OntologyClass"
 "biolink:OrganismalEntity"
 "biolink:Pathway"
 "biolink:PhenotypicFeature"
 "biolink:Protein"
 "biolink:SequenceFeature"
 "biolink:SexQualifier"
 "biolink:Source"
 "biolink:TaxonomicRank"
 "biolink:Unit"
 "biolink:AnatomicalEntity"
)

all_edgetypes=("biolink:related_to"
 "biolink:subclass_of"
 "biolink:part_of"
 "biolink:inverseOf"
 "biolink:subPropertyOf"
 "biolink:has_part"
 "biolink:has_participant"
 "biolink:has_unit"
 "biolink:preceded_by"
 "biolink:has_attribute"
 "biolink:positively_regulates"
 "biolink:negatively_regulates"
)

# Run
echo "*** General ontology counts:"

printf "%10s\t"  "All processed ontologies:"
ls -d $TX_PATH* | wc -l

printf "%10s\t"  "All successful JSON transforms:"
find $TX_PATH -name "*.json" | wc -l

printf "%10s\t"  "All successful KGX TSV transforms:"
find $TX_PATH -name "*_edges.tsv" | wc -l

printf "%10s\t"  "All transforms with KGX validation logs:"
find $TX_PATH -name "kgx_validate_*.log" | wc -l

printf "%10s\t"  "All transforms with ROBOT measure reports:"
find $TX_PATH -name "robot.measure" | wc -l

printf "%10s\t"  "All transforms with ROBOT validation reports:"
find $TX_PATH -name "robot.report" | wc -l

printf "%10s\t"  "Ontologies with failed transforms:"
find $TX_PATH -maxdepth 1 -type d -exec bash -c "echo -ne '{} '; ls '{}' | wc -l" \; | awk '$NF==1{print $1}'

echo "*** Transforms with at least one of the following errors:"
for ((i=0; i < ${#all_errortypes[@]}; i++))
do
    printf "%10s\t" "${all_errortypes[$i]}"
    grep -r -m1 --include \*.log "${all_errortypes[$i]}" $TX_PATH | wc -l
done

echo "*** Node type counts:"
for ((i=0; i < ${#all_nodetypes[@]}; i++))
do
    printf "%10s\t" "${all_nodetypes[$i]}"
    grep -r -m1 --include \*_nodes.tsv "${all_nodetypes[$i]}" $TX_PATH | wc -l
done

echo "*** Edge type counts (i.e., predicate types):"
for ((i=0; i < ${#all_edgetypes[@]}; i++))
do
    printf "%10s\t" "${all_edgetypes[$i]}"
    grep -r -m1 --include \*_edges.tsv "${all_edgetypes[$i]}" $TX_PATH | wc -l
done

echo "Complete."
