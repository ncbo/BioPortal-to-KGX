# run.py

"""
Tool to transform 4store data dumps
to KGX tsv nodes/edges.
Checks first row of each dump file to
verify if it contains a comment.
"""

import click

from bioportal_to_kgx.functions import examine_data_directory, \
                                        do_transforms, \
                                        validate_transforms

@click.command()
@click.option("--input",
                required=True,
                nargs=1,
                help="""Path to the 4store data dump - usually named data""")
@click.option("--kgx_validate",
                is_flag=True,
                help="""If used, will run the KGX validator after completing all transformations. 
                        Validation logs will be written to each output directory.""")
def run(input: str, kgx_validate: bool):

    data_filepaths = examine_data_directory(input)
    transform_status = do_transforms(data_filepaths)
    if kgx_validate:
        validate_transforms()

    print("Completed transforms:\n")
    print(transform_status)

if __name__ == '__main__':
  run()