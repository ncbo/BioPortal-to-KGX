#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests # type: ignore

BASE_ONTO_URL = "https://data.bioontology.org/ontologies/"

# These are the Biolink slots (keys) and their corresponding
# Bioportal metadata properties (values)
MD_HEADINGS = {'primary_knowledge_source':'name'}

def bioportal_metadata(ontoid: str, api_key: str) -> dict:
    """
    Retrieve metadata for the given ontology.
    Note that this requires a NCBO API key,
    to be passed in api_key.
    Returns a dict.
    :param outname: short identifier for the ontology,
                    to be used for API calls
    :param outdir: directory to write outfile to
    :param api_key: str, NCBO API key
    """
    desired_metadata = ['name']
    md = {key: None for key in desired_metadata}
        
    # Return content from the Ontology endpoint
    # http://data.bioontology.org/metadata/Ontology
    req_url = BASE_ONTO_URL + ontoid
    params = dict(apikey=api_key,display_context="False",include="all")

    print(f"Accessing {req_url}...")

    response = requests.get(req_url, params=params)
    print(response)

    content = response.json()
    if 'status' in content: #API doesn't return status on 200
        content = None
    
    # Reduce the content to just what we want
    if content:
        for md_type in desired_metadata:
            md[md_type] = content[md_type]

        print(f"Retrieved metadata for {ontoid} ({md['name']})")
    
    else:
        print(f"Could not retrieve metadata for {ontoid}.")

    return md

def check_header_for_md(filepath: str) -> bool:
    """
    Given a filename for a KGX edge or nodelist,
    checks for presence of metadata property names.
    :param filepath: str, path to KGX format file
    :return: bool, True if metadata fields appear present
    """

    have_md = False

    with open(filepath,'r') as infile:
        header = infile.readline()
    
    for heading in MD_HEADINGS:
        if heading in header:
            have_md = True

    return have_md

def manually_add_md(filepath: str, md: str) -> bool:
    """
    Given a filename for a KGX edge or nodelist,
    create a new header slot and add values to
    each entry.
    This only needs to happen if the
    node/edgefile already exists.
    Otherwise the metadata is added at graph
    file creation.
    :param filepath: str, path to KGX format file
    :param md: dict, the metadata
    :return: bool, True if successful
    """

    success = False

    out_filepath = filepath + ".tmp"

    try:
        with open(filepath,'r') as infile:
            out_header_split = (infile.readline().rstrip()).split("/t")
            with open(out_filepath,'w') as outfile:
                for heading in MD_HEADINGS:
                    out_header_split.append(heading)
                outfile.write("\t".join(out_header_split))
                for line in infile:
                    line_split = (line.rstrip()).split("/t")
                    for heading in MD_HEADINGS:
                        line_split.append(md[MD_HEADINGS[heading]])
                    outfile.write("\t".join(line_split))
        success = True
    except (IOError, KeyError) as e:
        print(f"Failed to write metadata to {filepath}: {e}")

    return success