#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests # type: ignore

BASE_ONTO_URL = "https://data.bioontology.org/ontologies/"

def bioportal_metadata(ontoid: str, outdir: str, api_key: str) -> None:
    """
    Retrieve metadata for the given ontology.
    Note that this requires a NCBO API key,
    to be passed in api_key.
    Writes metadata to the ontology's nodelist.
    :param outname: short identifier for the ontology,
                    to be used for API calls
    :param outdir: directory to write outfile to
    :param api_key: str, NCBO API key
    """

    # Return content from the Ontology endpoint
    # http://data.bioontology.org/metadata/Ontology
    req_url = BASE_ONTO_URL + ontoid
    params = dict(apikey=api_key,display_context="False",include="all")

    print(f"Accessing {req_url}...")

    response = requests.get(req_url, params=params)
    print(response)

    content = response.json()
    print(f"Retrieved metadata for {ontoid} ({content['name']})")

    # Load all nodes with kgx.transformer
    # Set 'provided_by' to the name of the ontology
    # then store the object
    # then save the object over the previous nodelist
    # or just use the kgx.cli with the --knowledge-sources flag?
