"""Main functions for transforming BP to KGX."""

import glob
import os
import re
import sys
import tempfile
from json import dump as json_dump

import kgx.cli  # type: ignore
import pandas as pd  # type: ignore

from universalizer.norm import clean_and_normalize_graph

from bioportal_to_kgx.bioportal_utils import (bioportal_metadata,
                                              check_header_for_md,
                                              manually_add_md)
from bioportal_to_kgx.robot_utils import (initialize_robot, relax_ontology,
                                          robot_measure, robot_remove,
                                          robot_report)
from bioportal_to_kgx.stats import make_transform_stats

TXDIR = "transformed"
NAMESPACE = "data.bioontology.org"
TARGET_TYPE = "ontologies"
MAPPING_DIR = "mappings"
PREFIX_DIR = "prefixes"
PREFIX_FILENAME = "bioportal-prefixes-curated.tsv"
PREF_PREFIX_FILENAME = "bioportal-preferred-prefixes.tsv"


def examine_data_directory(input: str, include_only: list, exclude: list):
    """
    Generate paths for all data files within a path, recursively.

    :param input: str for root of data dump
    :param include_only: if non-empty, only return these files
    :param exclude: if non-empty, don't return these files
    :return: list of file paths as strings
    """
    data_filepaths = []

    # Check if this path exists first.
    if not os.path.isdir(input):
        raise FileNotFoundError(f"Cannot find {input}.")

    print(f"Looking for records in {input}")

    including = False
    if len(include_only) > 0:
        print(f"Will only include the specified {len(include_only)} file(s).")
        including = True

    excluding = False
    if len(exclude) > 0:
        print(f"Will exclude the specified {len(exclude)} file(s).")
        excluding = True

    # Find all files, not including lone directory names
    for filepath in glob.iglob(input + "**/**", recursive=True):
        if len(os.path.basename(filepath)) == 28 \
                and filepath not in data_filepaths:
            if including and os.path.basename(filepath) not in include_only:
                continue
            if excluding and os.path.basename(filepath) in exclude:
                continue
            data_filepaths.append(filepath)

    if len(data_filepaths) > 0:
        print(f"{len(data_filepaths)} files found.")
    else:
        sys.exit("No files found at this path, or none mapping filters.")

    return data_filepaths


def do_transforms(
    paths: list,
    kgx_validate: bool,
    robot_validate: bool,
    pandas_validate: bool,
    get_bioportal_metadata: bool,
    ncbo_key: str,
    remap: bool,
    write_curies: bool,
) -> dict:
    """
    Do all the transformation operations.

    Given a list of file paths,
    first does pre-processing with ROBOT
    (relax only and convert to JSON), then
    uses KGX to transform each file
    to tsv node/edgelists.
    Parses header for each to get
    metadata.
    :param paths: list of file paths as strings
    :param kgx_validate: bool
    :param robot_validate: bool
    :param pandas_validate: bool
    :param get_bioportal_metadata: bool
    :param ncbo_key: str
    :param remap: bool
    :param write_curies: bool
    :return: dict of transform success/failure,
            with ontology names as keys,
            bools for values with success as True
    """
    if not os.path.exists(TXDIR):
        os.mkdir(TXDIR)

    print("Setting up ROBOT...")
    robot_path = os.path.join(os.getcwd(), "robot")
    robot_params = initialize_robot(robot_path)
    print(f"ROBOT path: {robot_path}")
    robot_env = robot_params[1]
    print(f"ROBOT evironment variables: {robot_env['ROBOT_JAVA_ARGS']}")

    txs_complete = {}
    txs_invalid = []

    tx_results = []  # A list of dicts

    print("Transforming all...")

    for filepath in paths:
        print(f"Starting on {filepath}")
        with open(filepath) as infile:
            header = (infile.readline()).rstrip()
            try:  # Throws IndexError if input header is malformed
                metadata = (header.split(NAMESPACE))[1]
            except IndexError:
                print(f"Header of {filepath} looks wrong...will skip.")
                continue
            metadata = metadata.lstrip("/")
            metadata_split = metadata.split("/")
            if metadata_split[0] == TARGET_TYPE:
                dataname = metadata_split[1]
                version = metadata_split[3]
                outname = f"{dataname}_{version}"
                outdir = os.path.join(TXDIR, "/".join(metadata_split[0:2]))
                outpath = os.path.join(outdir, outname)
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
                ok_to_transform = True
            else:
                continue

            # Check if the outdir already contains transforms
            # or if it contains a logfile - if not,
            # and the validate flag is True,
            # then validation is still required
            have_robot_report = False
            have_kgx_validation_log = False
            have_bioportal_metadata = False
            tx_filecount = 0
            filelist = os.listdir(outdir)
            for filename in filelist:
                if filename.endswith("nodes.tsv") \
                        or filename.endswith("edges.tsv"):
                    tx_filecount = tx_filecount + 1
                    if ok_to_transform:
                        print(f"Transform already present for {outname}")
                        ok_to_transform = False
                        txs_complete[outname] = True
                    # Check to see if metadata properties are in the header
                    if check_header_for_md(os.path.join(outdir, filename)):
                        print("BioPortal metadata present.")
                        have_bioportal_metadata = True
                if filename.endswith(".report"):
                    print(f"ROBOT report(s) present: {filename}")
                    have_robot_report = True
                if filename.endswith(".log"):
                    print(f"KGX validation log present: {filename}")
                    have_kgx_validation_log = True
            if pandas_validate and tx_filecount > 0:
                print("Validating graph files can be parsed...")
                if not pandas_validate_transform(outdir):
                    print(f"Validation did not complete for {outname}.")
                    txs_invalid.append(outname)
            if robot_validate and not have_robot_report and tx_filecount > 0:
                print(f"ROBOT reports not found for {outname} "
                      "- will generate.")
                get_robot_reports(filepath, outdir, robot_path, robot_env)
            if kgx_validate \
                    and not have_kgx_validation_log \
                    and tx_filecount > 0:
                print(f"KGX validation log not found for {outname} "
                      "- will validate.")
                kgx_validate_transform(outdir)
            if get_bioportal_metadata and not have_bioportal_metadata:
                print(f"BioPortal metadata not found for {outname} "
                      "- will retrieve.")
                onto_md = bioportal_metadata(dataname, ncbo_key)
                # If we fail to retrieve metadata, onto_md['name'] == None
                # Add metadata to existing transforms - just the edges for now
                # If we don't have transforms yet, metadata will be added below
                if (
                    onto_md["name"] != ""
                ):  # This will be empty string if metadata retrieval failed
                    for filename in filelist:
                        if filename.endswith("edges.tsv"):
                            print(f"Adding metadata to {outname}...")
                            if manually_add_md(os.path.join(outdir, filename),
                                               onto_md):
                                print("Complete.")
                            else:
                                print("Something went wrong during "
                                      "metadata writing.")

            # Need version of file w/o first line or KGX will choke
            # The file may be empty, but that doesn't mean the
            # relevant contents aren't somewhere in the data dump
            # So we write a placeholder if needed
            with tempfile.NamedTemporaryFile(mode="w", delete=False) \
                    as tempout:
                linecount = 0
                for line in infile:
                    tempout.write(line)
                    linecount = linecount + 1
                tempname = tempout.name

            if linecount == 0:
                print(f"File for {outname} is empty! Writing placeholder.")
                with open(outpath, "w") as outfile:
                    outfile.write("")
                    pass
                txs_complete[outname] = False
                continue

            if ok_to_transform:

                print(f"ROBOT: relax {outname}")
                relaxed_outpath = os.path.join(outdir,
                                               outname + "_relaxed.json")
                if relax_ontology(robot_path,
                                  tempname,
                                  relaxed_outpath,
                                  robot_env):
                    txs_complete[outname] = True
                else:
                    print("Encountered error during "
                          f"robot relax of {outname}.")

                    # We can try to fix it -
                    # this is usually a null value in a comment.
                    print("Will attempt to repair file and try again.")
                    repaired_outpath = remove_comments(tempname,
                                                       robot_path,
                                                       robot_env)
                    if relax_ontology(
                        robot_path,
                        repaired_outpath,
                        relaxed_outpath,
                        robot_env
                    ):
                        txs_complete[outname] = True
                    else:
                        print(
                            "Encountered unresolvable error during "
                            f"robot relax of {outname}."
                        )
                        print("Will skip.")
                        txs_complete[outname] = False
                        os.remove(tempout.name)
                        continue

                if robot_validate and txs_complete[outname]:
                    print("Generating ROBOT reports...")
                    if not get_robot_reports(filepath,
                                             outdir,
                                             robot_path,
                                             robot_env):
                        print(f"Could not get ROBOT reports for {outname}.")

                if (
                    get_bioportal_metadata
                    and not have_bioportal_metadata
                    and onto_md["name"]
                ):
                    primary_knowledge_source = onto_md["name"]
                    have_bioportal_metadata = True
                else:
                    primary_knowledge_source = "False"

                print(f"KGX transform {outname}")
                try:
                    kgx.cli.transform(
                        inputs=[relaxed_outpath],
                        input_format="obojson",
                        output=outpath,
                        output_format="tsv",
                        stream=True,
                        knowledge_sources=[
                            ("aggregator_knowledge_source",
                                "BioPortal"),
                            ("primary_knowledge_source",
                                primary_knowledge_source),
                        ],
                    )
                    txs_complete[outname] = True
                except ValueError as e:
                    print("Encountered error during "
                          f"KGX transform of {outname}: {e}")

                    # We can try to fix it - this is usually a malformed CURIE
                    # (or something that looks like a CURIE)
                    print("Will attempt to repair file and try again.")
                    repaired_outpath = remove_bad_curie(relaxed_outpath)
                    try:
                        kgx.cli.transform(
                            inputs=[repaired_outpath],
                            input_format="obojson",
                            output=outpath,
                            output_format="tsv",
                            stream=True,
                            knowledge_sources=[
                                ("aggregator_knowledge_source",
                                    "BioPortal"),
                                ("primary_knowledge_source",
                                    primary_knowledge_source),
                            ],
                        )
                        txs_complete[outname] = True
                    except ValueError as e:
                        print("Encountered error during "
                              f"KGX transform of {outname}: {e}")

                # Validation
                if kgx_validate and txs_complete[outname]:
                    print("Validating graph files with KGX...")
                    if not kgx_validate_transform(outdir):
                        print(f"Validation did not complete for {outname}.")
                        txs_complete[outname] = False
                        txs_invalid.append(outname)

            # Wrapped normalization steps all go here.
            # Take the 'remap' and 'write_curies' params
            # and pass the SSSOM map directory in the former case
            print("Normalizing graph...")

            maps = []
            if remap:
                maps = [os.join(MAPPING_DIR, fn) for fn in
                        os.listdir(MAPPING_DIR) if
                        os.isfile(os.join(MAPPING_DIR, fn))]

            if not clean_and_normalize_graph(filepath=outdir,
                                             compressed=False,
                                             maps=maps,
                                             update_categories=write_curies,
                                             oak_lookup=False):
                print(f"Normalization did not complete for {outname}.")

            # One last mandatory validation step - can pandas load it?
            # Also gets node and edge counts in the process.
            if txs_complete[outname]:
                print("Validating graph files with pandas...")
                nodecount, edgecount = pandas_validate_transform(outdir)
                if (nodecount, edgecount) == (0, 0):
                    print(f"Validation did not complete for {outname}.")
                    txs_complete[outname] = False
                    txs_invalid.append(outname)

            # Remove the tempfile
            os.remove(tempout.name)

            # Update the results dict
            if outname not in txs_invalid and txs_complete[outname]:
                status = "OK"
            else:
                status = "FAIL"
            tx_result = {"id": dataname,
                         "status": status,
                         "nodecount": nodecount,
                         "edgecount": edgecount}
            tx_results.append(tx_result)

    # Notify about any invalid transforms (i.e., completed but broken somehow)
    if len(txs_invalid) > 0:
        print(f"The following transforms may have issues:{txs_invalid}")

    make_transform_stats(tx_results, "onto_status.yaml")

    # TODO: clean up all remaining placeholders
    return txs_complete


def pandas_validate_transform(in_path: str) -> tuple:
    """
    Validate transforms by parsing them with pandas.

    Will raise a caught error
    if there's an issue with format rendering
    the graph files un-parsible.
    Also gets node and edge counts.
    :param in_path: str, path to directory
    :return: tuple of (nodecount, edgecount).
    If file is invalid, both values are zero.
    """
    tx_filepaths = []
    for filepath in os.listdir(in_path):
        if filepath.endswith("nodes.tsv") or \
                filepath.endswith("edges.tsv"):
            tx_filepaths.append(os.path.join(in_path, filepath))

    if len(tx_filepaths) == 0:
        print(f"Could not find graph files in {in_path}.")
        return False
    try:
        linecount = 0
        for filepath in tx_filepaths:
            file_iter = pd.read_csv(
                filepath,
                dtype=str,
                chunksize=10000,
                low_memory=False,
                keep_default_na=False,
                quoting=3,
                lineterminator="\n",
                delimiter="\t",
            )
            for chunk in file_iter:
                linecount = linecount + len(chunk)
            if filepath.endswith("edges.tsv"):
                edgecount = linecount
            if filepath.endswith("nodes.tsv"):
                nodecount = linecount
            print(f"Graph file {filepath} parses OK.")

    except (pd.errors.ParserError, pd.errors.EmptyDataError) as e:
        print(f"Encountered parsing error in {filepath}: {e}")
        nodecount = 0
        edgecount = 0

    counts = (nodecount, edgecount)

    return counts


def get_robot_reports(
    filepath: str, outpath_dir: str, robot_path: str, robot_env: dict
) -> bool:
    """
    Run both the ROBOT 'report' and 'measure' on an obojson.

    Saves both to the same directory as
    the input ontology.
    Runs a convert command first to ensure
    ROBOT can parse the input.
    Returns True if successful,
    otherwise False - though any errors detected
    in the target ontology by the report command
    will yield False, too.
    :param filepath: path to the *original* ontology dump file
    :param outpath_dir: directory where output
    :param robot_path: path to ROBOT itself
    :param robot_env: ROBOT environment parameters
    :return: True if success
    """
    success = True

    report_path = os.path.join(outpath_dir, "robot.report")
    measure_path = os.path.join(outpath_dir, "robot.measure")

    # Will state 'Report failed!' if any errors present
    if not robot_report(
        robot_path=robot_path,
        input_path=filepath,
        output_path=report_path,
        robot_env=robot_env,
    ):
        success = False

    if not robot_measure(
        robot_path=robot_path,
        input_path=filepath,
        output_path=measure_path,
        robot_env=robot_env,
    ):
        success = False

    return success


def kgx_validate_transform(in_path: str) -> bool:
    """
    Run KGX validation on a single set of node/edge files.

    Takes a input directory containing a transformed
    ontology. Writes log to that directory.
    :param in_path: str, path to directory
    :return: True if complete, False otherwise
    """
    tx_filepaths = []

    # Find node/edgefiles
    # and check if they are empty
    for filepath in os.listdir(in_path):
        if filepath[-3:] == "tsv":
            if not is_file_too_short(os.path.join(in_path, filepath)):
                tx_filepaths.append(os.path.join(in_path, filepath))

    if len(tx_filepaths) == 0:
        print(f"All transforms in {in_path} are blank or very short.")
        return False

    tx_filename = os.path.basename(tx_filepaths[0])
    tx_name = "_".join(tx_filename.split("_", 2)[:2])
    log_path = os.path.join(in_path, f"kgx_validate_{tx_name}.log")

    # kgx validate output isn't working for some reason
    # so there are some workarounds here
    with open(log_path, "w") as log_file:
        try:
            json_dump(
                (
                    kgx.cli.validate(
                        inputs=tx_filepaths,
                        input_format="tsv",
                        input_compression=None,
                        stream=True,
                        output=None,
                    )
                ),
                log_file,
                indent=4,
            )
            print(f"Wrote validation errors to {log_path}")
            return True
        except TypeError as e:
            print(f"Error while validating {tx_name}: {e}")
            return False


def is_file_too_short(filepath: str) -> bool:
    """
    Check if a file contains only an empty line.

    Also check if it's otherwise very short
    (i.e., it has a non-zero size but is still empty,
    or is only a few lines).
    :param filepath: str, path to file
    :return: bool, True if file is blank or too short
    """
    with open(filepath, "r") as infile:
        for count, _ in enumerate(infile):
            count = count + 1

    if count >= 2:
        return False
    else:
        return True


def remove_bad_curie(filepath: str) -> str:
    """
    Remove malformed CURIEs.

    Given the path to an obojson with a
    CURIE causing KGX to fail transforms,
    remove the offending prefix.
    Save a new file and return.
    :param filepath: str, path to file
    :return: path to repaired file
    """
    repaired_filepath = filepath + ".repaired"

    with open(filepath, "r") as infile:
        with open(repaired_filepath, "w") as outfile:
            for line in infile:
                for pattern in ["file:C:", "file:"]:
                    line = re.sub(pattern, "", line)
                outfile.write(line)

    return repaired_filepath


def remove_comments(filepath: str, robot_path: str, robot_env: dict) -> str:
    """
    Remove comments.

    Given the path to an obojson file,
    remove all comment triples.
    They usually have a predicate like
    <http://www.w3.org/2000/01/rdf-schema#comment>
    Save a new file and return.
    The robot_remove function in robot_utils
    does most of the work here,
    but it also needs the output format to be OWL
    first to ensure the final JSON is as expected.
    :param filepath: str, path to file
    :param robot_path: path to ROBOT itself
    :param robot_env: ROBOT environment parameters
    :return: path to repaired file
    """
    repaired_filepath = (os.path.splitext(filepath)[0]) + "nocomments.owl"

    comment_term = "rdfs:comment"

    robot_remove(
        robot_path=robot_path,
        input_path=filepath,
        output_path=repaired_filepath,
        term=comment_term,
        robot_env=robot_env,
    )

    return repaired_filepath
