"""Functions to produce transform statistics."""

import yaml


def make_transform_stats(results: list, output_file: str) -> None:
    """Produce a simple YAML output containing select transform statistics.

    :param results: list of dicts, each with
    key:value of [id:str, status:str,
    nodecount:int, edgecount:int]
    :return: None
    """
    stats = {"ontologies": results}

    with open(output_file, 'w') as stats_file:
        stats_file.write(yaml.dump(stats,
                                   default_flow_style=False,
                                   sort_keys=False))
