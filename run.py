# run.py

"""
Tool to transform 4store data dumps
to KGX tsv nodes/edges.
Checks first row of each dump file to
verify if it contains a comment.
"""

import os
import glob
import click

import kgx.cli

OUTDIR = "transformed"
NAMESPACE = "data.bioontology.org"
TARGET_TYPE = "ontologies"

@click.command()
@click.option("--input",
               required=True,
               nargs=1,
               help="""Path to the 4store data dump - usually named data""")
def run(input: str):

    data_filepaths = examine_data_directory(input)
    set_up_outdirs(data_filepaths)
    do_transforms(data_filepaths)

def examine_data_directory(input: str):
    """
    Given a path, generates paths for all data files
    within, recursively.
    :param input: str for root of data dump
    :return: list of file paths as strings
    """

    data_filepaths = []

    print(f"Looking for records in {input}")

    # Find all files, not including lone directory names
    for filepath in glob.iglob(input + '**/**', recursive=True):
        if len(os.path.basename(filepath)) == 28:
            data_filepaths.append(filepath)
    
    print(f"{len(data_filepaths)} files found.")
    
    return data_filepaths

def set_up_outdirs(paths: list) -> None:
    """
    Given a list of file paths,
    sets up output directories.
    :param paths: list of file paths as strings
    """

    print("Setting up output directories...")

    if not os.path.exists(OUTDIR):
        os.mkdir(OUTDIR)

    for filepath in paths:
        newpath = "/".join((filepath.split("/"))[-3:-1])
        newpath = os.path.join(OUTDIR,newpath)
        print(newpath)
        if not os.path.exists(newpath):
            os.makedirs(newpath)

def do_transforms(paths: list) -> None:
    """
    Given a list of file paths,
    uses KGX to transform each file
    to tsv node/edgelists.
    Parses header for each to get
    metadata.
    :param paths: list of file paths as strings
    """

    print("Transforming...")

    for filepath in paths:
        with open(filepath) as infile:
            header = (infile.readline()).rstrip()
            metadata = (header.split(NAMESPACE))[1]
            metadata = metadata.lstrip('/')
            metadata_split = (metadata.split("/"))
            if metadata_split[0] == TARGET_TYPE:
                dataname = metadata_split[1]
                version = metadata_split[3]
                outname = f"{dataname}_{version}" 
                outpath = os.path.join(OUTDIR,metadata[0:2],outname)
            else:
                continue
        
        # Still need to remove first line or KGX will choke

        kgx.cli.transform(inputs=filepath,
                          input_format='nt',
                          output=outpath,
                          output_format='tsv')
            

if __name__ == '__main__':
  run()