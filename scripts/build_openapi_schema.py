"""build_openapi_schema.py."""


import json
import logging
import pathlib
import sys

from jsonschema_tools import set_all_nested

LOGGER = logging.getLogger(__name__)


def main(src: str, dst: str) -> None:
    """Main."""
    print("Building OpenAPI schema...")
    print(src, dst)

    # NOTE: DO NOT CHANGE THE CONTENTS OF THE SCHEMA, ONLY ASSEMBLE.
    #
    # ANY MODIFICATIONS SHOULD BE MADE TO **ORIGINAL FILES**
    # (NOT THE AUTO-GENERATED FILE) AND COMMITTED.

    with open(src) as f:
        spec = json.load(f)

    # build paths entries
    if isinstance(spec["paths"], str) and spec["paths"].startswith(
        "GHA_CI_MAKE_PATHS_FROM_DIR"
    ):
        # ex: "GHA_CI_MAKE_PATHS_FROM_DIR ./paths/"
        paths_dir = pathlib.Path(src).parent / pathlib.Path(spec["paths"].split()[1])
        print(paths_dir)
        spec["paths"] = {}  # *** OVERRIDE ANYTHING THAT WAS HERE ***

        # assemble
        for fpath in paths_dir.iterdir():
            print(fpath)
            with open(fpath) as f:
                if fpath.stem == "root":
                    path_pattern = "/"
                else:
                    path_pattern = "/" + fpath.stem.replace(".", "/")
                print(fpath, path_pattern)
                spec["paths"][path_pattern] = json.load(f)  # type: ignore[index]

    # replace 'GHA_CI_INGEST_FILE_CONTENTS' with the targeted file's contents
    # ex: GHA_CI_INGEST_FILE_CONTENTS ../db/TaskDirective.json
    def ingest_file(d, k):
        parts = d[k].split()
        fpath = parts[1]
        options = parts[2:]
        with open(fpath) as f:
            d[k] = json.load(f)
            # grab options
            for opt in options:
                okey, oval = opt.split("=")
                d[k][okey] = json.loads(oval)

    set_all_nested(
        spec,
        ingest_file,
        lambda d, k: isinstance(d[k], str)
        and d[k].startswith("GHA_CI_INGEST_FILE_CONTENTS"),
    )

    # format neatly
    spec["paths"] = dict(sorted(spec["paths"].items()))
    with open(dst, "w") as f:
        json.dump(spec, f, indent=4)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
