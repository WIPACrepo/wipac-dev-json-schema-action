"""modify_rest_path_schemas.py."""


import json
import logging
import pathlib
import re
import sys

import jsonschema_tools

LOGGER = logging.getLogger(__name__)

NEW_400 = {
    "description": "invalid request arguments",
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {
                    "code": {"description": "http error code", "type": "integer"},
                    "error": {"description": "http error reason", "type": "string"},
                },
                "required": ["code", "error"],
            }
        }
    },
}

NEW_404 = {
    "description": "not found",
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {
                    "code": {"description": "http error code", "type": "integer"},
                    "error": {"description": "http error reason", "type": "string"},
                },
                "required": ["code", "error"],
            }
        }
    },
}


def main(dpath: str) -> None:
    """Main."""
    print("Modifying REST path schemas...")
    print(dpath)

    # GO!
    for fpath in pathlib.Path(dpath).iterdir():
        print(fpath)
        with open(fpath) as f:
            spec = json.load(f)

        # find "responses" keys, then set their "400" keys
        def set_responses_400(d, k):
            d["responses"].update({"400": NEW_400})

        jsonschema_tools.set_all_nested(
            spec,
            set_responses_400,
            lambda d, k: k == "responses" and d["responses"].get("400") != NEW_400,
        )

        # find "responses" keys, then set their "404" keys
        def set_responses_404(d, k):
            d["responses"].update({"404": NEW_404})

        # Using re.findall() to extract strings inside {}
        # ex: example.{id}.json
        if re.findall(r"\{([^/{}]+)\}", str(fpath)):
            jsonschema_tools.set_all_nested(
                spec,
                set_responses_404,
                lambda d, k: k == "responses" and d["responses"].get("404") != NEW_404,
            )

        jsonschema_tools.set_default_array_minitems(spec, 0)
        jsonschema_tools.set_default_additionalproperties(spec, False)  # after error-codes
        jsonschema_tools.set_default_minproperties(spec, 0)

        # format neatly
        with open(fpath, "w") as f:
            json.dump(spec, f, indent=4)
        with open(fpath, "a") as f:  # else json.dump removes trailing newline
            f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1])
