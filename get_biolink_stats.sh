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

# Run

echo -e "Ontology\tNodeCount\tEdgeCount"
for entry in "$TX_PATH"*
do
    base=$(basename $entry)

    nodefile=$(find -wholename "$entry/*_nodes.tsv")
    if [ -f "$nodefile" ]; then
        nodecount=$(wc -l < $nodefile | bc)
        nodecount=$(($nodecount - 1)) # Header
    else
        nodecount='0'
    fi

    edgefile=$(find -wholename "$entry/*_edges.tsv")
    if [ -f "$edgefile" ]; then
        edgecount=$(wc -l < $edgefile | bc)
        edgecount=$(($edgecount - 1)) # Header
    else
        edgecount='0'
    fi

    echo -e "$base\t$nodecount\t$edgecount"
done

echo "Complete."
