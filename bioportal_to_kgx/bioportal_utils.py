#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests # type: ignore

BASE_ONTO_URL = "https://data.bioontology.org/ontologies/"

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
    :return: bool, True if metadata fiels appear present
    """

    have_md = False

    md_headings = ['primary_knowledge_source']
    with open(filepath,'r') as infile:
        header = infile.readline()
    
    for heading in md_headings:
        if heading in header:
            have_md = True

    return have_md