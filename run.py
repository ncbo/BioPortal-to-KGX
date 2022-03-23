# run.py

"""
Tool to transform 4store data dumps
to KGX tsv nodes/edges.
Checks first row of each dump file to
verify if it contains a comment.
"""

import sys
import click

from bioportal_to_kgx.functions import examine_data_directory, do_transforms # type: ignore

@click.command()
@click.option("--input",
                required=True,
                nargs=1,
                help="""Path to the 4store data dump - usually named data""")
@click.option("--kgx_validate",
                is_flag=True,
                help="""If used, will run the KGX validator after completing each transformation. 
                        Validation logs will be written to each output directory.
                        If an existing transform is found without a validation log,
                        a new validation will be run.""")
@click.option("--robot_validate",
                is_flag=True,
                help="""If used, will run ROBOT measure and ROBOT report for each transformation. 
                        Logs will be written to each output directory.
                        If an existing transform is found without ROBOT logs,
                        a new validation will be run.""")
@click.option("--get_bioportal_metadata",
                is_flag=True,
                help="""If used, will retrieve metadata from BioPortal. 
                        Requires Internet connection and NCBO API key.
                        (From BioPortal account page.)
                        Specify the API key in the --ncbo_key parameter.
                        Metadata is stored in its own KGX TSV nodefile, e.g., BTO_1_nodes_metadata.tsv""")
@click.option("--ncbo_key",
                help="""Key for the NCBO API.""")
@click.option("--include_only",
                callback=lambda _,__,x: x.split(',') if x else [],
                help="""One or more ontologies to retreive and transform, and only these,
                     comma-delimited and named by their hashed file ID, e.g., dabd4d902360003975fb25ae56f8.""")
@click.option("--exclude",
                callback=lambda _,__,x: x.split(',') if x else [],
                help="""One or more ontologies to exclude from transforms,
                     comma-delimited and named by their hashed file ID, e.g., dabd4d902360003975fb25ae56f8.""")

def run(input: str, kgx_validate: bool, robot_validate: bool, get_bioportal_metadata: bool,
        ncbo_key=None, include_only=[], exclude=[]):

    if get_bioportal_metadata and not ncbo_key:
      sys.exit("Cannot access BioPortal metadata without API key. Specify in --ncbo_key parameter.")

    data_filepaths = examine_data_directory(input, include_only, exclude)
    transform_status = do_transforms(data_filepaths, kgx_validate, robot_validate, 
                                      get_bioportal_metadata, ncbo_key)

    successes = ", ".join(list(dict(filter(lambda elem: elem[1], transform_status.items()))))
    failures = ", ".join(list(dict(filter(lambda elem: not elem[1], transform_status.items()))))
    print(f"Successful transforms: {successes}")
    print(f"Failed transforms: {failures}")

if __name__ == '__main__':
  run()