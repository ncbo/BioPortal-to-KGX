# functions.py

import os
import sys
import glob
import tempfile
import re
from json import dump as json_dump

import kgx.cli # type: ignore
import pandas as pd # type: ignore
from sssom.parsers import read_sssom_table # type: ignore
from sssom.util import MappingSetDataFrame # type: ignore

from bioportal_to_kgx.robot_utils import initialize_robot, relax_ontology, robot_remove, robot_report, robot_measure  # type: ignore
from bioportal_to_kgx.bioportal_utils import bioportal_metadata, check_header_for_md, manually_add_md # type: ignore

TXDIR = "transformed"
NAMESPACE = "data.bioontology.org"
TARGET_TYPE = "ontologies"
MAPPING_DIR = "mappings"
PREFIX_DIR = "prefixes"
PREFIX_FILENAME = "bioportal-prefixes-curated.tsv"
PREF_PREFIX_FILENAME = "bioportal-preferred-prefixes.tsv"

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

def do_transforms(paths: list,
                    kgx_validate: bool, 
                    robot_validate: bool,
                    pandas_validate: bool,
                    get_bioportal_metadata: bool, 
                    ncbo_key: str,
                    remap_types: bool,
                    write_curies: bool) -> dict:
    """
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
    :param remap_types: bool
    :param write_curies: bool
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
    txs_invalid = []

    # If planning to do maps, load them first
    if remap_types:
        #TODO: instead of making a dict, merge SSSOMs with sssom.util.merge_msdf
        print(f"Loading type maps from {MAPPING_DIR}/")
        type_map = {} # type: ignore
        all_map_paths = []
        for filepath in os.listdir(MAPPING_DIR):
            if filepath.endswith("sssom.tsv"):
                this_table = read_sssom_table(os.path.join(MAPPING_DIR,filepath))
                all_map_paths.append(this_table)
        # Convert the SSSOM maps to a dict of originaltype:newtype
        for msdf in all_map_paths:
            for i, row in msdf.df.iterrows():
                subj = None
                obj = None
                for k, v in row.iteritems():
                    if k == 'subject_id':
                        subj = v
                    if k == 'object_id':
                        obj = v
                    if subj and obj:
                        type_map[subj] = obj
        print(f"Loaded {len(type_map)} mappings.")

    # If planning to write new CURIEs, need to load prefixes first
    if write_curies:
        print(f"Loading prefix maps from {PREFIX_DIR}/")
        prefix_map = {} # type: ignore
        pref_prefix_map = {} # type: ignore
        with open(os.path.join(PREFIX_DIR,PREFIX_FILENAME)) as prefix_file:
            prefix_file.readline() # Skip header
            for line in prefix_file:
                splitline = (line.rstrip()).split("\t")
                ontoid = splitline[0]
                prefix = splitline[1]
                delim = splitline[2]
                native = splitline[3]
                if ontoid in prefix_map:
                    prefix_map[ontoid]["prefixes"].append([prefix, delim, native])
                else:
                    prefix_map[ontoid] = {"prefixes":[[prefix, delim, native]]}
        with open(os.path.join(PREFIX_DIR,PREF_PREFIX_FILENAME)) as prefix_file:
            prefix_file.readline() # Skip header
            for line in prefix_file:
                splitline = (line.rstrip()).split("\t")
                pref_prefix_map[splitline[0]] = splitline[1]

        print(f"Loaded prefixes for {len(prefix_map)} ontologies.")
        print(f"Loaded preferred prefixes for {len(pref_prefix_map)} ontologies.")
        

    print("Transforming all...")

    for filepath in paths:
        print(f"Starting on {filepath}")
        with open(filepath) as infile:
            header = (infile.readline()).rstrip()
            try:    # Throws IndexError if input header is malformed
                metadata = (header.split(NAMESPACE))[1]
            except IndexError:
                print(f"Header of {filepath} looks wrong...will skip.")
                continue
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
            have_robot_report = False
            have_kgx_validation_log = False
            have_bioportal_metadata = False
            tx_filecount = 0
            filelist = os.listdir(outdir)
            for filename in filelist:
                if (filename.endswith("nodes.tsv") or filename.endswith("edges.tsv")):
                    tx_filecount = tx_filecount + 1
                    if ok_to_transform:
                        print(f"Transform already present for {outname}")
                        ok_to_transform = False
                        txs_complete[outname] = True
                    # Check to see if metadata properties are in the header
                    if check_header_for_md(os.path.join(outdir,filename)):
                        print(f"BioPortal metadata present.")
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
                print(f"ROBOT reports not found for {outname} - will generate.")
                get_robot_reports(filepath, outdir, robot_path, robot_env)
            if kgx_validate and not have_kgx_validation_log and tx_filecount > 0:
                print(f"KGX validation log not found for {outname} - will validate.")
                kgx_validate_transform(outdir)
            if get_bioportal_metadata and not have_bioportal_metadata:
                print(f"BioPortal metadata not found for {outname} - will retrieve.")
                onto_md = bioportal_metadata(dataname, ncbo_key)
                # If we fail to retrieve metadata, onto_md['name'] == None
                # Add metadata to existing transforms - just the edges for now
                # If we don't have transforms yet, metadata will be added below
                if onto_md['name'] != '': # This will be empty string if metadata retrieval failed
                    for filename in filelist:
                        if filename.endswith("edges.tsv"):
                            print(f"Adding metadata to {outname}...")
                            if manually_add_md(os.path.join(outdir,filename), onto_md):
                                print("Complete.")
                            else:
                                print("Something went wrong during metadata writing.")
            # If writing CURIEs is requested, do it now
            if write_curies and tx_filecount > 0:
                print(f"Will write new CURIEs for nodes in {outname}.")
                if not update_nodes("curies", outdir, prefix_map, pref_prefix_map):
                    print(f"CURIE writing did not complete for {outname}.")
            # If remapping to Biolink is requested, do it now
            if remap_types and tx_filecount > 0:
                print(f"Will remap node/edge types in {outname} to Biolink Model.")
                if not update_nodes("types", outdir, type_map):
                    print(f"Type mapping did not complete for {outname}.")

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
                    print(f"Encountered error during robot relax of {outname}.")

                    # We can try to fix it - 
                    # this is usually a null value in a comment.
                    print("Will attempt to repair file and try again.")
                    repaired_outpath = remove_comments(tempname, robot_path, robot_env)
                    if relax_ontology(robot_path, 
                                        repaired_outpath,
                                        relaxed_outpath,
                                        robot_env):
                        txs_complete[outname] = True
                    else:
                        print(f"Encountered unresolvable error during robot relax of {outname}.")
                        print("Will skip.")
                        txs_complete[outname] = False
                        os.remove(tempout.name)
                        continue
                
                if robot_validate and txs_complete[outname]:
                    print("Generating ROBOT reports...")
                    if not get_robot_reports(filepath, outdir, robot_path, robot_env):
                        print(f"Could not get ROBOT reports for {outname}.")

                if get_bioportal_metadata and not have_bioportal_metadata \
                    and onto_md['name']:
                    primary_knowledge_source = onto_md['name']
                    have_bioportal_metadata = True
                else:
                    primary_knowledge_source = 'False'

                print(f"KGX transform {outname}")
                try:
                    kgx.cli.transform(inputs=[relaxed_outpath],
                            input_format='obojson',
                            output=outpath,
                            output_format='tsv',
                            stream=True,
                            knowledge_sources=[("aggregator_knowledge_source", "BioPortal"),
                                                ("primary_knowledge_source", primary_knowledge_source)])
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
                            stream=True,
                            knowledge_sources=[("aggregator_knowledge_source", "BioPortal"),
                                                ("primary_knowledge_source", primary_knowledge_source)])
                        txs_complete[outname] = True
                    except ValueError as e:
                        print(f"Encountered error during KGX transform of {outname}: {e}")

                # Validation
                if kgx_validate and txs_complete[outname]:
                    print("Validating graph files with KGX...")
                    if not kgx_validate_transform(outdir):
                        print(f"Validation did not complete for {outname}.")
                        txs_complete[outname] = False
                        txs_invalid.append(outname)

                # Writing CURIEs
                if write_curies and txs_complete[outname]:
                    print(f"Will write new CURIEs for nodes in {outname}.")
                    if not update_nodes("curies", outdir, prefix_map, pref_prefix_map):
                        print(f"CURIE writing did not complete for {outname}.")
                        txs_complete[outname] = False
                        txs_invalid.append(outname)

                # Remapping to Biolink
                if remap_types and txs_complete[outname]:
                    print(f"Will remap node/edge types in {outname} to Biolink Model.")
                    if not update_nodes("types", outdir, type_map):
                        print(f"Type mapping did not complete for {outname}.")
                        txs_complete[outname] = False
                        txs_invalid.append(outname)
                
                # One last mandatory validation step - can pandas load it?
                print("Validating graph files with pandas...")
                if not pandas_validate_transform(outdir):
                    print(f"Validation did not complete for {outname}.")
                    txs_complete[outname] = False
                    txs_invalid.append(outname)

            # Remove the tempfile
            os.remove(tempout.name)

    # Notify about any invalid transforms (i.e., completed but broken somehow)
    if len(txs_invalid) > 0:
        print(f"The following transforms may have issues:{txs_invalid}")

    # TODO: clean up all remaining placeholders
    return txs_complete

def pandas_validate_transform(in_path: str) -> bool:
    """
    Validates transforms by parsing them
    with pandas. Will raise a caught error
    if there's an issue with format rendering
    the graph files un-parsible.
    :param in_path: str, path to directory
    :return: True if complete, False otherwise
    """

    tx_filepaths = []
    for filepath in os.listdir(in_path):
        if filepath.endswith('.tsv'):
            tx_filepaths.append(os.path.join(in_path,filepath))

    if len(tx_filepaths) == 0:
        print(f"Could not find graph files in {in_path}.")
        return False
    try:
        for filepath in tx_filepaths:
            file_iter = pd.read_csv(
                filepath,
                dtype=str,
                chunksize=10000,
                low_memory=False,
                keep_default_na=False,
                quoting=3,
                lineterminator="\n",
                delimiter="\t")
            for chunk in file_iter:
                pass    #Just making sure it loads
        print(f"Graph file {filepath} parses OK.")
        success = True
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as e:
        print(f"Encountered parsing error in {filepath}: {e}")
        success = False
    
    return success


def get_robot_reports(filepath: str, outpath_dir: str, robot_path: str, robot_env: dict) -> bool:
    """
    Given the path to an obojson file,
    run both the ROBOT 'report' and 'measure'
    commands.
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

    report_path = os.path.join(outpath_dir,"robot.report") 
    measure_path = os.path.join(outpath_dir,"robot.measure")

    # Will state 'Report failed!' if any errors present
    if not robot_report(robot_path=robot_path, 
                input_path=filepath, 
                output_path=report_path, 
                robot_env=robot_env):
                success = False 
    
    if not robot_measure(robot_path=robot_path, 
                input_path=filepath, 
                output_path=measure_path, 
                robot_env=robot_env):
                success = False

    return success

def kgx_validate_transform(in_path: str) -> bool:
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

def update_nodes(operation: str, in_path: str, operation_map: dict, extra_map: dict={}) -> bool:
    """
    Checks on node and edgefile
    suitability for updating node details.
    :param operation: str, one of "curies" or "types"
    :param in_path: str, path to directory
    :param operation_map: dict of mappings to use
    :param extra_map: additional maps, if needed by further operations
    :return: True if complete, False otherwise
    """

    tx_filepaths = []

    success = True

    # Find node/edgefiles
    for filepath in os.listdir(in_path):
        if filepath[-3:] == 'tsv':
            if not is_file_too_short(os.path.join(in_path,filepath)):
                tx_filepaths.append(os.path.join(in_path,filepath))

    if len(tx_filepaths) == 0:
        print(f"No transforms found for {in_path}.")
        success = False
    elif len(tx_filepaths) < 2:
        print(f"Could not find node or edgelist for {in_path}.")
        success = False

    filepaths = {}
    for filepath in tx_filepaths:
        if filepath.endswith("_nodes.tsv"):
            filepaths["nodelist"] = filepath
        elif filepath.endswith("_edges.tsv"):
            filepaths["edgelist"] = filepath
    
    if success:
        if operation == "curies":
            ontoid = os.path.basename(in_path)
            if ontoid not in operation_map:
                print(f"Don't know native prefixes for {ontoid} - will search others.")
            if not write_curies(filepaths, ontoid, operation_map, extra_map):
                success = False
        elif operation == "types":
            if not append_new_types(filepaths, operation_map):
                success = False

    return success

def append_new_types(filepaths: dict, type_map: dict) -> bool:
    """
    Given a filename for a KGX edge or nodelist,
    update node or edge types.
    Requires both node and edgelist.
    Updates types to be more specific 
    Biolink Model types.
    New types are *appended* to existing types.
    :param filepath: str, path to KGX format file
    :param type_map: dict of strs, with keys as type to find
                    and values as type to append
    :return: bool, True if successful
    """

    success = False

    nodepath = filepaths["nodelist"]
    edgepath = filepaths["edgelist"]

    outnodepath = nodepath + ".tmp"
    outedgepath = edgepath + ".tmp"

    remap_these_nodes = {}

    try:
        with open(nodepath,'r') as innodefile, \
            open(edgepath, 'r') as inedgefile:
            with open(outnodepath,'w') as outnodefile, \
                open(outedgepath, 'w') as outedgefile:
                for line in inedgefile:
                    line_split = (line.rstrip()).split("\t")
                    # Check for edges representing node types to be remapped
                    if line_split[4].endswith("hasSTY"):
                        node_id = ":".join(((line_split[1]).rsplit("/",2))[-2:])
                        type_id = ":".join(((line_split[3]).rsplit("/",2))[-2:])
                        remap_these_nodes[node_id] = type_id
                    outedgefile.write("\t".join(line_split) + "\n")
                for line in innodefile:
                    line_split = (line.rstrip()).split("\t")
                    try:
                        node_id = ":".join(((line_split[0]).rsplit("/",2))[-2:])
                        # Check if the node id is a type we recognize
                        # e.g., the IRI is 'http://purl.bioontology.org/ontology/STY/T120'
                        if node_id in type_map:
                            line_split[1] = line_split[1] + "|" + type_map[node_id]
                        # Check if we saw a type assignment among the edges already
                        if node_id in remap_these_nodes:
                            line_split[1] = line_split[1] + "|" + type_map[remap_these_nodes[node_id]]
                    except KeyError:
                        pass
                    
                    # Before writing, remove any redundant types
                    # and OntologyClass, unless it's the only type
                    try:
                        this_type_list = line_split[1].split("|")
                        this_type_list = list(set(this_type_list))
                        if "biolink:OntologyClass" in this_type_list and \
                            len(this_type_list) > 1:
                            this_type_list.remove("biolink:OntologyClass")
                        line_split[1] = "|".join(this_type_list)
                    except KeyError:
                        pass

                    outnodefile.write("\t".join(line_split) + "\n")
                
        os.replace(outnodepath,nodepath)
        os.replace(outedgepath,edgepath)
        success = True
    except (IOError, KeyError) as e:
        print(f"Failed to remap node/edge types for {nodepath} and/or {edgepath}: {e}")
        success = False

    return success

def write_curies(filepaths: dict, ontoid: str, prefix_map: dict, pref_prefix_map: dict) -> bool:
    """
    Update node id field in an edgefile 
    and each corresponding subject/object 
    node in the corresponding edges 
    to have a CURIE, where the prefix is 
    the ontology ID and the class is
    inferred from the IRI.
    :param in_path: str, path to directory
    :param ontoid: the Bioportal ID of the ontology
    :return: True if complete, False otherwise
    """

    success = False

    nodepath = filepaths["nodelist"]
    edgepath = filepaths["edgelist"]

    outnodepath = nodepath + ".tmp"
    outedgepath = edgepath + ".tmp"

    update_these_nodes = {}

    try:
        with open(nodepath,'r') as innodefile, \
            open(edgepath, 'r') as inedgefile:
            with open(outnodepath,'w') as outnodefile, \
                open(outedgepath, 'w') as outedgefile:
                for line in innodefile:
                    updated_node = False
                    line_split = (line.rstrip()).split("\t")
                    node_iri = line_split[0]
                    if ontoid in prefix_map:
                        for prefix in prefix_map[ontoid]["prefixes"]:
                            if node_iri.startswith(prefix[0]):
                                split_iri = node_iri.rsplit(prefix[1],1)
                                if ontoid in pref_prefix_map:
                                    ontoid = pref_prefix_map[ontoid]
                                if len(split_iri) == 2:
                                    new_curie = f"{ontoid}:{split_iri[1]}"
                                else:
                                    new_curie = f"{ontoid}:"
                                line_split[0] = new_curie
                                update_these_nodes[node_iri] = new_curie
                                updated_node = True
                                continue
                    # If we don't have a native prefix OR this is a foreign prefix
                    # then look at other ontologies
                    if ontoid not in prefix_map or not updated_node:
                        for prefix_set in prefix_map:
                            for prefix in prefix_map[prefix_set]["prefixes"]:
                                 if node_iri.startswith(prefix[0]):
                                    split_iri = node_iri.rsplit(prefix[1],1)
                                    if prefix_set in pref_prefix_map:
                                        prefix_set = pref_prefix_map[prefix_set]
                                    if len(split_iri) == 2:
                                        new_curie = f"{prefix_set}:{split_iri[1]}"
                                    else:
                                        new_curie = f"{prefix_set}:"
                                    line_split[0] = new_curie
                                    update_these_nodes[node_iri] = new_curie
                                    continue
                    outnodefile.write("\t".join(line_split) + "\n")
                for line in inedgefile:
                    line_split = (line.rstrip()).split("\t")
                    # Check for edges containing nodes to be updated
                    if line_split[1] in update_these_nodes:
                        line_split[1] = update_these_nodes[line_split[1]]
                    if line_split[3] in update_these_nodes:
                        line_split[3] = update_these_nodes[line_split[3]]  
                    outedgefile.write("\t".join(line_split) + "\n")
                
        os.replace(outnodepath,nodepath)
        os.replace(outedgepath,edgepath)
        success = True
    except (IOError, KeyError) as e:
        print(f"Failed to write CURIES for {nodepath} and/or {edgepath}: {e}")
        success = False

    return success

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
                for pattern in ["file:C:","file:"]:
                    line = re.sub(pattern, "", line)
                outfile.write(line)

    return repaired_filepath

def remove_comments(filepath: str, robot_path: str, robot_env: dict) -> str:
    """
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

    robot_remove(robot_path=robot_path, 
                input_path=filepath, 
                output_path=repaired_filepath, 
                term=comment_term, 
                robot_env=robot_env)

    return repaired_filepath
