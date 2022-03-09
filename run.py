# run.py

"""
Tool to transform 4store data dumps
to KGX tsv nodes/edges.
Checks first row of each dump file to
verify if it contains a comment.
"""

import click

from bioportal_to_kgx.functions import examine_data_directory, do_transforms # type: ignore \ 

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
def run(input: str, kgx_validate: bool):

    data_filepaths = examine_data_directory(input)
    transform_status = do_transforms(data_filepaths, kgx_validate)

    successes = ", ".join(list(dict(filter(lambda elem: elem[1], transform_status.items()))))
    failures = ", ".join(list(dict(filter(lambda elem: not elem[1], transform_status.items()))))
    print(f"Successful transforms: {successes}")
    print(f"Failed transforms: {failures}")

if __name__ == '__main__':
  run()