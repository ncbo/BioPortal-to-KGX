#!/bin/bash
# Get transformation stats for BioPortal ontologies,
# as counts of nodes and edges per ontology
# and as counts of nodes/edges per Biolink class.
# Output is TSV with ontologies in rows
# and count types in columns.

TX_PATH="./transformed/ontologies/"

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

all_classes+=( "${all_nodetypes[@]}" "${all_edgetypes[@]}" )
all_classes_joined=$(printf "\t%s" "${all_classes[@]}")

# Run

echo -e "Ontology\tNodeCount\tEdgeCount\t$all_classes_joined"
for entry in "$TX_PATH"*
do
    base=$(basename $entry)

    nodefile=$(find -wholename "$entry/*_nodes.tsv")
    declare -A node_type_counts
    if [ -f "$nodefile" ]; then
        nodecount=$(wc -l < $nodefile | bc)
        nodecount=$(($nodecount - 1)) # Header
        for ((i=0; i < ${#all_nodetypes[@]}; i++))
        do
            this_type_count=$(grep ${all_nodetypes[$i]} $nodefile | wc -l)
            node_type_counts[$i]=$this_type_count
        done
    else
        nodecount='0'
        for ((i=0; i < ${#all_nodetypes[@]}; i++))
        do
            node_type_counts[$i]='0'
        done
    fi
    node_type_counts_joined=$(printf "\t%s" "${node_type_counts[@]}")

    edgefile=$(find -wholename "$entry/*_edges.tsv")
    declare -A edge_type_counts
    if [ -f "$edgefile" ]; then
        edgecount=$(wc -l < $edgefile | bc)
        edgecount=$(($edgecount - 1)) # Header
        for ((i=0; i < ${#all_edgetypes[@]}; i++))
        do
            this_type_count=$(grep ${all_edgetypes[$i]} $edgefile | wc -l)
            edge_type_counts[$i]=$this_type_count
        done
    else
        edgecount='0'
        for ((i=0; i < ${#all_edgetypes[@]}; i++))
        do
            edge_type_counts[$i]='0'
        done
    fi
    edge_type_counts_joined=$(printf "\t%s" "${edge_type_counts[@]}")

    echo -e "$base\t$nodecount\t$edgecount\t$node_type_counts_joined\t$edge_type_counts_joined"
done

echo "Complete."
