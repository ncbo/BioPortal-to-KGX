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
    prefixes=$(cut -f1 $file | rev | cut -d"#" -f2- | rev | sort | uniq)
    delimiter=$(printf "#")

    # If this delimiter didn't appear to work, try another
    prefix_count=$(wc -w <<< "$prefixes")
    too_many=10
    if (( $prefix_count > $too_many ))
    then
        prefixes=$(cut -f1 $file | rev | cut -d"/" -f2- | rev | sort | uniq)
        delimiter=$(printf "/")
    fi

    # If this delimiter didn't appear to work, try another
    # Keeping in mind that : is the standard CURIE delimiter
    # at least for OBO imports
    prefix_count=$(wc -w <<< "$prefixes")
    too_many=10
    if (( $prefix_count > $too_many ))
    then
        prefixes=$(cut -f1 $file | rev | cut -d":" -f2- | rev | sort | uniq)
        delimiter=$(printf ":")
    fi

    # Ran out of standard delimiters, so we may have some strangeness in IRI format
    prefix_count=$(wc -w <<< "$prefixes")
    too_many=100
    if (( $prefix_count > $too_many ))
    then
        prefixes=$(cut -f1 $file | rev | cut -f2 | rev | sort | uniq)
        delimiter=$(printf "OTHER")
    fi

    for prefix in $prefixes
    do 
        native=$(printf "unknown")
        printf "$ontology\t$prefix\t$delimiter\t$native\n"
    done
done
