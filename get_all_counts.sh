#!/bin/bash
# Get all node and edge counts for BioPortal ontologies
#

TX_PATH="./transformed/ontologies/"

echo "*** Finding all node counts..."
ALL_NODE_FILES=$(find transformed/ontologies/ -name *_nodes.tsv)
for f in $ALL_NODE_FILES
do
    printf "%10s\t" "$f"
    nodecounts=$(sort $f | wc -l)
    printf "%10s\n" "$nodecounts"
done

echo "*** Finding all edge counts..."
ALL_EDGE_FILES=$(find transformed/ontologies/ -name *_edges.tsv)
for f in $ALL_EDGE_FILES
do
    printf "%10s\t" "$f"
    edgecounts=$(sort $f | wc -l)
    printf "%10s\n" "$edgecounts"
done
