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
import tempfile

import kgx.cli

TXDIR = "transformed"
NAMESPACE = "data.bioontology.org"
TARGET_TYPE = "ontologies"

@click.command()
@click.option("--input",
               required=True,
               nargs=1,
               help="""Path to the 4store data dump - usually named data""")
def run(input: str):

    data_filepaths = examine_data_directory(input)
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

def do_transforms(paths: list) -> None:
    """
    Given a list of file paths,
    uses KGX to transform each file
    to tsv node/edgelists.
    Parses header for each to get
    metadata.
    :param paths: list of file paths as strings
    """

    if not os.path.exists(TXDIR):
        os.mkdir(TXDIR)

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
            else:
                continue
            
            # Need version of file w/o first line or KGX will choke
            # The file may be empty!
            with tempfile.NamedTemporaryFile(mode = "w", delete=False) as tempout:
                linecount = 0
                for line in infile:
                    tempout.write(line)
                    linecount = linecount +1
                tempname = tempout.name
                print(tempname)

            if linecount > 0:
                print(f"Transforming {outname}")
                kgx.cli.transform(inputs=[tempname],
                        input_format='nt',
                        output=outpath,
                        output_format='tsv')
            else:
                print(f"File for {outname} is empty! Writing placeholder.")
                with open(outpath, 'w') as outfile:
                    pass
            
            os.remove(tempout.name)
            
if __name__ == '__main__':
  run()