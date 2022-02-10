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

from kgx.cli.cli_utils import transform


@click.command()
@click.option("--input",
               required=True,
               nargs=1,
               help="""Path to the 4store data dump - usually named data""")
def run(input: str):

    data_filepaths = examine_data_directory(input)
    set_up_outdirs(data_filepaths)

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

    outdir = "transformed"

    print("Setting up output directories...")

    if not os.path.exists(outdir):
        os.mkdir(outdir)

    for filepath in paths:
        newpath = "/".join((filepath.split("/"))[-3:-1])
        newpath = os.path.join(outdir,newpath)
        print(newpath)
        if not os.path.exists(newpath):
            os.makedirs(newpath)

if __name__ == '__main__':
  run()