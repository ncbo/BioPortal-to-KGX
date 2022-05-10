#!/bin/bash
# Get details of all IRIs across all Bioportal transforms
# This creates bioportal-prefixes.tsv
#

TX_PATH="./transformed/ontologies/"

NODE_FILES=$(find $TX_PATH -name *_nodes.tsv)

# Run
echo "ontology	prefix	delimiter	native"
for file in $NODE_FILES
do
    dirpath=${file%/*}/
    ontology=$(basename "$dirpath" | tr -d '\n')
    prefix=$(cut -f1 $file)
    delimiter=$(printf "a_delimiter")
    native=$(printf "true_or_false")
    printf "$ontology\t$prefix\t$delimiter\t$native\n"
done
