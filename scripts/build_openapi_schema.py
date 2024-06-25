"""build_openapi_schema.py."""

import argparse
import json
import logging
import pathlib

from jsonschema_tools import set_all_nested

LOGGER = logging.getLogger(__name__)


def get_path_pattern(
    dunder_path: str,
    dunder_paths_no_vprefix: list[str],
    maj_version: int,
) -> str:
    """Assemble the path pattern from the dunder path with other additions."""
    translated_path = dunder_path.replace("__", "/")

    if dunder_path in dunder_paths_no_vprefix:
        return translated_path

    if translated_path == "/" or translated_path == "root":
        return f"/v{maj_version}/"

    return f"/v{maj_version}/{translated_path}"


def build_paths_entries(src: str, spec: dict, dunder_paths_no_vprefix: list[str]):
    """Build out the 'paths' entries in the spec."""
    maj_version = int(spec["info"]["version"].split(".", maxsplit=1)[0])

    # ex: "GHA_CI_MAKE_PATHS_FROM_DIR ./paths/"
    paths_dir = pathlib.Path(src).parent / pathlib.Path(spec["paths"].split()[1])
    print(paths_dir)
    spec["paths"] = {}  # *** OVERRIDE ANYTHING THAT WAS HERE ***

    # assemble
    for fpath in paths_dir.iterdir():  # -> FileNotFoundError
        print(fpath)
        with open(fpath) as f:
            path_pattern = get_path_pattern(
                fpath.stem,
                dunder_paths_no_vprefix,
                maj_version,
            )
            print(fpath, path_pattern)
            spec["paths"][path_pattern] = json.load(f)  # type: ignore[index]


def build_spec(
    src: str,
    dst: str,
    dunder_paths_no_vprefix: list[str],
) -> None:
    """Main."""
    print("Building OpenAPI schema...")
    print(src, dst)
    pathlib.Path(dst).parent.mkdir(parents=True, exist_ok=True)

    # NOTE: DO NOT CHANGE THE CONTENTS OF THE SCHEMA, ONLY ASSEMBLE.
    #
    # ANY MODIFICATIONS SHOULD BE MADE TO **ORIGINAL FILES**
    # (NOT THE AUTO-GENERATED FILE) AND COMMITTED.

    with open(src) as f:
        spec = json.load(f)

    if isinstance(spec["paths"], str) and spec["paths"].startswith(
        "GHA_CI_MAKE_PATHS_FROM_DIR"
    ):
        build_paths_entries(src, spec, dunder_paths_no_vprefix)

    # replace 'GHA_CI_INGEST_FILE_CONTENTS' with the targeted file's contents
    # ex: GHA_CI_INGEST_FILE_CONTENTS ../db/TaskDirective.json
    def ingest_file(d, k):
        parts = d[k].split()
        _fpath = pathlib.Path(src).parent / parts[1]
        if not _fpath.exists():
            raise FileNotFoundError(_fpath)
        _options = parts[2:]
        with open(_fpath) as f:
            d[k] = json.load(f)
            # grab options
            for opt in _options:
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
    with open(dst, "w+") as f:
        json.dump(spec, f, indent=4)


def main() -> None:

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--src",
        required=True,
        help="Path to the pre-built spec",
    )
    parser.add_argument(
        "--dst",
        required=True,
        help="Path to put the built spec",
    )
    parser.add_argument(
        "--dunder-paths-no-vprefix",
        nargs="*",
        help="see action.yaml for more details",
    )
    args = parser.parse_args()

    build_spec(args.src, args.dst, args.dunder_paths_no_vprefix)


if __name__ == "__main__":
    main()
