#!/bin/bash
# Get all node and edge types for BioPortal ontologies
#

TX_PATH="./transformed/ontologies/"

echo "*** Finding all node types..."
ALL_NODE_FILES=$(find transformed/ontologies/ -name *_nodes.tsv)
ALL_NODE_TYPES=""
for f in $ALL_NODE_FILES
do
    printf "%10s\t" "$f"
    nodetypes=$(cut -f 2 $f | xargs -n1 | sort | uniq | xargs)
    printf "%10s\n" "$nodetypes"
    ALL_NODE_TYPES+=$nodetypes 
done

echo "All node types:"
echo $ALL_NODE_TYPES 

echo "*** Finding all edge types..."
ALL_EDGE_FILES=$(find transformed/ontologies/ -name *_edges.tsv)
ALL_EDGE_TYPES=""
for f in $ALL_EDGE_FILES
do
    printf "%10s\t" "$f"
    edgetypes=$(cut -f 2 $f | xargs -n1 | sort | uniq | xargs)
    printf "%10s\n" "$edgetypes"
    ALL_EDGE_TYPES+=$edgetypes
done

echo "All edge types:"
echo $ALL_EDGE_TYPES 