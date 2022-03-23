#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

BASE_ONTO_URL = "https://data.bioontology.org/ontologies/"

def bioportal_metadata(outname: str, outdir: str, api_key: str) -> None:
    """
    Retrieve metadata for the given ontology.
    Note that this requires a NCBO API key,
    to be passed in api_key.
    Writes metadata as nodelist to outdir.
    :param outname: short identifier for the ontology,
                    to be used for API calls
    :param outdir: directory to write outfile to
    :param api_key: str, NCBO API key
    """

    req_url = BASE_ONTO_URL + outname
    params = dict(key=api_key)

    print(f"Accessing {req_url}...")

    response = requests.get(req_url, params=params)
    print(response)

    content = response.json()
