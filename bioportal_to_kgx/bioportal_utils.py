"""Functions for interfacing with Bioportal."""

import os
from typing import List

import requests  # type: ignore

BASE_ONTO_URL = "https://data.bioontology.org/ontologies/"

# Mapping from Biolink slots (keys) to a custom value
# assembled from metadata
MD_HEADINGS = {"primary_knowledge_source": "full_name"}


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
    md = {}
    missing_pages = []  # type: List[str]

    # Return content from the Ontology endpoint
    # http://data.bioontology.org/metadata/Ontology
    # Get the base ontology record and the latest_submission record
    for rec_type in ["", "latest_submission"]:
        req_url = f"{BASE_ONTO_URL}{ontoid}/{rec_type}"
        params = dict(apikey=api_key, display_context="False", include="all")
        print(f"Accessing {req_url}...")

        response = requests.get(req_url, params=params)
        print(response)

        if response.status_code != 200:
            content = None
            missing_pages.append(req_url)
        else:
            content = response.json()

        # Reduce the content to just what we want
        if content:
            if rec_type == "":
                for md_type in ["name", "ontologyType"]:
                    md[md_type] = content[md_type]
            elif rec_type == "latest_submission":
                for md_type in ["submissionId", "creationDate"]:
                    md[md_type] = content[md_type]

        # Assemble the full name
        if all(md_type in md for md_type in ["name", "submissionId"]):
            md["full_name"] = f"{md['name']} - submission {md['submissionId']}"
        elif "name" in md:
            md["full_name"] = md["name"]

    if len(missing_pages) == 0:
        print(f"Retrieved metadata for {ontoid} ({md['name']})")
    else:
        print(f"Tried metadata retrieval for {ontoid}, "
              f"but failed on {missing_pages}")
        md["name"] = ""

    return md


def check_header_for_md(filepath: str) -> bool:
    """
    Check for presence of metadata property names.

    Takes a filename for a KGX edge or nodelist.
    :param filepath: str, path to KGX format file
    :return: bool, True if metadata fields appear present
    """
    have_md = False

    with open(filepath, "r") as infile:
        header = infile.readline()

    for heading in MD_HEADINGS:
        if heading in header:
            have_md = True

    return have_md


def manually_add_md(filepath: str, md: str) -> bool:
    """
    Create a new header slot and add values to node/edgelist.

    Takes a filename for the KGX edge or nodelist,
    for each entry.
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
        with open(filepath, "r") as infile:
            out_header_split = ((infile.readline()).rstrip()).split("/t")
            with open(out_filepath, "w") as outfile:
                for heading in MD_HEADINGS:
                    out_header_split.append(heading)
                outfile.write("\t".join(out_header_split) + "\n")
                for line in infile:
                    line_split = (line.rstrip()).split("\t")
                    for heading in MD_HEADINGS:
                        line_split.append(md[MD_HEADINGS[heading]])
                    outfile.write("\t".join(line_split) + "\n")
        os.replace(out_filepath, filepath)
        success = True
    except (IOError, KeyError) as e:
        print(f"Failed to write metadata to {filepath}: {e}")

    return success
