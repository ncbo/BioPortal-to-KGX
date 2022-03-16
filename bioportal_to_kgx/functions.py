# functions.py

import os
import sys
import glob
import tempfile
import re
from json import dump as json_dump

import kgx.cli # type: ignore

from bioportal_to_kgx.robot_utils import initialize_robot, relax_ontology # type: ignore

TXDIR = "transformed"
NAMESPACE = "data.bioontology.org"
TARGET_TYPE = "ontologies"

def examine_data_directory(input: str, include_only: list, exclude: list):
    """
    Given a path, generates paths for all data files
    within, recursively.
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
    for filepath in glob.iglob(input + '**/**', recursive=True):
        if len(os.path.basename(filepath)) == 28 and \
            filepath not in data_filepaths:
            if including and os.path.basename(filepath) not in include_only:
                continue
            if excluding and os.path.basename(filepath) in exclude:
                continue
            data_filepaths.append(filepath)
    
    if len(data_filepaths) > 0:
        print(f"{len(data_filepaths)} files found.")
    else:
        sys.exit("No files found at this path!")
    
    return data_filepaths

def do_transforms(paths: list, validate: bool) -> dict:
    """
    Given a list of file paths,
    first does pre-processing with ROBOT
    (relax only and convert to JSON), then
    uses KGX to transform each file
    to tsv node/edgelists.
    Parses header for each to get
    metadata.
    :param paths: list of file paths as strings
    :param validate: bool, do validations if True
    :return: dict of transform success/failure,
            with ontology names as keys,
            bools for values with success as True
    """

    if not os.path.exists(TXDIR):
        os.mkdir(TXDIR)

    print("Setting up ROBOT...")
    robot_path = os.path.join(os.getcwd(),"robot")
    robot_params = initialize_robot(robot_path)
    print(f"ROBOT path: {robot_path}")
    robot_env = robot_params[1]
    print(f"ROBOT evironment variables: {robot_env['ROBOT_JAVA_ARGS']}")

    txs_complete = {}

    print("Transforming all...")

    for filepath in paths:
        print(f"Starting on {filepath}")
        with open(filepath) as infile:
            header = (infile.readline()).rstrip()
            metadata = (header.split(NAMESPACE))[1]
            metadata = metadata.lstrip('/')
            metadata_split = (metadata.split("/"))
            if metadata_split[0] == TARGET_TYPE:
                dataname = metadata_split[1]
                version = metadata_split[3]
                outname = f"{dataname}_{version}"
                outdir = os.path.join(TXDIR,"/".join(metadata_split[0:2]))
                outpath = os.path.join(outdir,outname)
                if not os.path.exists(outdir):
                    os.makedirs(outdir)
                ok_to_transform = True
            else:
                continue
            
            # Check if the outdir already contains transforms
            # or if it contains a logfile - if not,
            # and the validate flag is True,
            # then validation is still required
            have_validation_log = False
            tx_filecount = 0
            filelist = os.listdir(outdir)
            for filename in filelist:
                if (filename.endswith("nodes.tsv") or filename.endswith("edges.tsv")):
                    tx_filecount = tx_filecount + 1
                    if ok_to_transform:
                        print(f"Transform already present for {outname}")
                        ok_to_transform = False
                if filename.endswith(".log"):
                    print(f"Validation log present: {filename}")
                    have_validation_log = True
            if validate and not have_validation_log and tx_filecount > 0:
                print(f"Validation log not found for {outname} - will validate.")
                validate_transform(outdir)
                    
            # Need version of file w/o first line or KGX will choke
            # The file may be empty, but that doesn't mean the
            # relevant contents aren't somewhere in the data dump
            # So we write a placeholder if needed
            with tempfile.NamedTemporaryFile(mode = "w", delete=False) as tempout:
                linecount = 0
                for line in infile:
                    tempout.write(line)
                    linecount = linecount +1
                tempname = tempout.name

            if linecount == 0:
                print(f"File for {outname} is empty! Writing placeholder.")
                with open(outpath, 'w') as outfile:
                    pass
                txs_complete[outname] = False
                continue

            if ok_to_transform:

                print(f"ROBOT: relax {outname}")
                relaxed_outpath = os.path.join(outdir,outname+"_relaxed.json")
                if relax_ontology(robot_path, 
                                        tempname,
                                        relaxed_outpath,
                                        robot_env):
                    txs_complete[outname] = True
                else:
                    print(f"ROBOT relax of {outname} failed - skipping.")
                    txs_complete[outname] = False
                    os.remove(tempout.name)
                    continue

                print(f"KGX transform {outname}")
                try:
                    kgx.cli.transform(inputs=[relaxed_outpath],
                            input_format='obojson',
                            output=outpath,
                            output_format='tsv',
                            knowledge_sources=[("aggregator_knowledge_source", "BioPortal"),
                                                ("primary_knowledge_source", "False")])
                    txs_complete[outname] = True
                except ValueError as e:
                    print(f"Encountered error during KGX transform of {outname}: {e}")

                    # We can try to fix it - this is usually a malformed CURIE
                    # (or something that looks like a CURIE)
                    print("Will attempt to repair file and try again.")
                    repaired_outpath = remove_bad_curie(relaxed_outpath)
                    try:
                        kgx.cli.transform(inputs=[repaired_outpath],
                            input_format='obojson',
                            output=outpath,
                            output_format='tsv',
                            knowledge_sources=[("aggregator_knowledge_source", "BioPortal"),
                                                ("primary_knowledge_source", "False")])
                        txs_complete[outname] = True
                    except ValueError as e:
                        print(f"Encountered error during KGX transform of {outname}: {e}")

                if validate and txs_complete[outname]:
                    print("Validating...")
                    if not validate_transform(outdir):
                        print(f"Validation did not complete for {outname}.")

            # Remove the tempfile
            os.remove(tempout.name)

    return txs_complete

def validate_transform(in_path: str) -> bool:
    """
    Runs KGX validation on a single set of
    node/edge files, given a input directory
    containing a transformed ontology. 
    Writes log to that directory.
    :param in_path: str, path to directory
    :return: True if complete, False otherwise
    """

    tx_filepaths = []

    # Find node/edgefiles
    # and check if they are empty
    for filepath in os.listdir(in_path):
        if filepath[-3:] == 'tsv':
            if not is_file_too_short(os.path.join(in_path,filepath)):
                tx_filepaths.append(os.path.join(in_path,filepath))

    if len(tx_filepaths) == 0:
        print(f"All transforms in {in_path} are blank or very short.")
        return False
    
    tx_filename = os.path.basename(tx_filepaths[0])
    tx_name = "_".join(tx_filename.split("_", 2)[:2])
    log_path = os.path.join(in_path,f'kgx_validate_{tx_name}.log')

    # kgx validate output isn't working for some reason
    # so there are some workarounds here
    with open(log_path, 'w') as log_file:
        try:
            json_dump((kgx.cli.validate(inputs=tx_filepaths,
                        input_format="tsv",
                        input_compression=None,
                        stream=True,
                        output=None)),
                        log_file,
                        indent=4)
            print(f"Wrote validation errors to {log_path}")
            return True
        except TypeError as e:
            print(f"Error while validating {tx_name}: {e}")
            return False

def is_file_too_short(filepath: str) -> bool:
    """
    Checks if a file contains only an empty line
    or is otherwise very short 
    (i.e., it has a non-zero size but is still empty,
    or is only a few lines).
    :param filepath: str, path to file
    :return: bool, True if file is blank or too short
    """

    with open(filepath, 'r') as infile:
        for count, line in enumerate(infile):
            pass
    
    if count >= 2:
        return False
    else:
        return True

def remove_bad_curie(filepath: str) -> str:
    """
    Given the path to an obojson with a
    CURIE causing KGX to fail transforms,
    remove the offending prefix.
    Save a new file and return.
    :param filepath: str, path to file
    :return: path to repaired file
    """

    repaired_filepath = filepath + ".repaired"

    with open(filepath, 'r') as infile:
        with open(repaired_filepath, 'w') as outfile:
            for line in infile:
                line = re.sub("file:", "", line)
                outfile.write(line)

    return repaired_filepath