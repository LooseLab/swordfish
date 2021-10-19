from itertools import chain, repeat
from pprint import pformat, pprint
from typing import Tuple
import re
from pathlib import Path

import toml

from swordfish.utils import get_barcode_kits, get_device, write_toml_file


def condition_me(deplete: bool) -> dict:
    """
    Return the unclassified and classified conditions for the TOML
    Returns
    -------
    dict
        Dictionary of condition
    """
    depletey = "stop_receiving" if not deplete else "unblock"
    base_condition = {
        "classified": {
            "name": "classified",
            "control": False,
            "min_chunks": 0,
            "max_chunks": 2,
            "targets": [],
            "single_on": depletey,
            "multi_on": depletey,
            "single_off": depletey,
            "multi_off": depletey,
            "no_seq": "proceed",
            "no_map": "proceed",
        },
        "unclassified": {
            "name": "unclassified_reads",
            "control": False,
            "min_chunks": 0,
            "max_chunks": 2,
            "targets": [],
            "single_on": "unblock",
            "single_off": "unblock",
            "multi_on": "unblock",
            "multi_off": "unblock",
            "no_seq": "proceed",
            "no_map": "proceed",
        },
    }
    return base_condition


def get_mapping_behaviors(choice: str) -> Tuple:
    """
    Get the behaviours for the TOML file depending on single on single off
    Parameters
    ----------
    choice: str
        One of deplete or enrich

    Returns
    -------

    """


def validate_barcode_kit(barcode_kit: str, address: str) -> bool:
    """
    Validate the user provided barcode kit if Guppy info is present
    Parameters
    ----------
    barcode_kit: str
        The used barcode kit
    address: str
        Guppy hosting address
    Returns
    -------
    bool - valid (or not)

    """
    try:
        return True if barcode_kit in get_barcode_kits(address) or not get_barcode_kits(address) else False
    except RuntimeError as e:
        print(repr(e))
        return True


def setup_caller_settings() -> dict:
    """
    Setup Guppy basecaller settings
    Returns
    -------
    dict
        Dict of caller settings
    """
    print("\nTell me about your guppy client...\n")
    quests = [
        (
            "address",
            "What is the address it lives at? Mine, for example, lives at localhost. ",
        ),
        ("port", "What port should I call at? usually Guppy instances prefer 5555. "),
    ]
    dicty = {}
    for key, quest in quests:
        prompts = chain(
            [quest], repeat("Invalid choice, please type one of - Deplete, Enrich "),
        )
        replies = map(input, prompts)
        deplete = next(replies)
        dicty[key] = deplete
    return dicty


def barcoding_adventure(args, version) -> dict:
    """
    Build your own barcoding adventure! Results not guaranteed
    Returns
    -------
    dict
        The dictionary containing the toml json for your barcoding experiment
    pathlib.Path
        The path to the TOML file
    """

    toml_path = args.toml
    # todo could be alot drier
    print("\nIt's dangerous to go alone, take this TOML file!\n")
    choices = ("deplete", "enrich", "Deplete", "Enrich")
    prompts = chain(
        ["Do you wish to deplete or enrich? "],
        repeat("Invalid choice, please type one of - Deplete, Enrich "),
    )
    replies = map(input, prompts)
    deplete = next(filter(choices.__contains__, replies))
    print(deplete)

    caller_settings_dict = setup_caller_settings()

    y_n = ("Y", "N")
    prompts = chain(
        ["\nAccept multi mappings? Y/N "],
        repeat("Invalid choice, please type one of - Y, N "),
    )
    replies = map(input, prompts)
    multi_map = bool(next(filter(y_n.__contains__, replies)))
    print(multi_map)
    multi_map = True if multi_map == "Y" else False

    prompts = chain(
        [f"\nComma seperated barcodes to {deplete} - eg. 40,20,19 "],
        repeat(
            "Invalid format, please type barcode digits, comma seperated, no whitespace! "
        ),
    )
    replies = map(input, prompts)
    pat = re.compile(r"(\d{2},*$)|(\d{2},)+\d{2}$|(\d{2},)+\d{2},$")
    barcode_string = next(filter(pat.fullmatch, replies))
    print(f"Valid selection! {barcode_string}")

    address = f"{caller_settings_dict['address']}:{caller_settings_dict['port']}"
    prompts = chain(
        ["\nWhich mighty barcode kit did you yield?"], repeat(f"Not in your Guppy Library! One of"
                                                              f"{get_barcode_kits(address, names=True)}"),
    )
    replies = map(input, prompts)
    # todo the thing about multiple barcode kits
    # todo barcode kit validation
    barcode_kit = next(filter(lambda reply: validate_barcode_kit(reply, address), replies))
    print(barcode_kit)

    print("\nThere's just the question of the reference... Where doth it dwell? ")
    prompts = chain(["Enter a path: "], repeat("This path doesn't exist! Try again: "))
    replies = map(input, prompts)
    paths = map(Path, replies)
    reference_file = next(filter(Path.exists, paths))
    deplete = True if deplete.lower() == "deplete" else False
    print(reference_file)
    toml_body = {
        f"barcode{barcode_number}": {
            "name": f"barcode{barcode_number}",
            "control": False,
            "min_chunks": 0,
            "max_chunks": 4,
            "targets": [],
            "single_on": "unblock" if deplete else "stop_receiving",
            "single_off": "stop_receiving",
            "multi_on": "unblock"
            if deplete
            else "stop_receiving"
            if multi_map
            else "unblock",
            "multi_off": "stop_receiving",
            "no_seq": "proceed",
            "no_map": "proceed",
        }
        for barcode_number in barcode_string.split(",")
    }
    toml_preamble = {
        "conditions": {"reference": str(reference_file)},
        "caller_settings": {
            "config_name": "dna_r9.4.1_450bps_fast",
            "host": caller_settings_dict["address"],
            "port": caller_settings_dict["port"],
            "barcode_kits": [barcode_kit],
        },
    }
    classified_body = condition_me(deplete)
    classified_body.update(toml_body)
    toml_preamble["conditions"].update(classified_body)
    toml_path = toml_path
    # todo seriousise this
    if not str(toml_path).endswith("_practice"):
        toml_path = f"{toml_path}_practice"
    with open(toml_path, "w") as fh:
        toml.dump(toml_preamble, fh)
    return toml_preamble


def update_barcoding_adventure(args, version):
    """
    Update an existing TOML file ane write out a live file
    Parameters
    ----------
    args: argparse.Namespace
        The arguments provided
    position: minknow_api.Connection
        Connection to minknow
    version: str
        The swordfish version

    Returns
    -------
    None

    """

    toml_path = args.toml
    print("\nSo you want to update your TOML file.\n")
    dicty = {}
    quests = [
        (
            "remove",
            "Do you want to remove or add barcode(s) to the TOML file? ",
            {"add", "remove"}
        ),
        ("deplete",
         "Do you wish to deplete or enrich for these barcodes? ", {"deplete", "enrich"}),
        ("multi",
         "Accept Multi Mappings? Y/N ", {"y", "n"}),
        ("barcode_string", "Barcodes, as a comma seperated list, no whitespace! Example, 40,29,10 ", ""),
    ]

    for key, quest, choices in quests:
        print(dicty)
        if key == "deplete" and dicty["remove"] == "remove" or key == "multi" and dicty["remove"] == "remove":
            continue
        choices_string = f"Please type one of {'/'.join(choices)} " if choices else ""
        prompts = chain(
            [quest], repeat(f"Invalid choice. Try again. {choices_string} "),
        )
        replies = map(input, prompts)
        if key == "barcode_string":
            pat = re.compile(r"(\d{2},*$)|(\d{2},)+\d{2}$|(\d{2},)+\d{2},$")
            reply_value = next(filter(pat.fullmatch, replies))
        else:
            replies = map(str.lower, replies)
            reply_value = next(filter(choices.__contains__, replies))
        dicty[key] = reply_value

    remove = dicty["remove"] == "remove"
    with open(toml_path, "r") as fh:
        data = toml.load(fh)
    barcodes = [f"barcode{barcode}" for barcode in dicty["barcode_string"].split(",")]
    for barcode in barcodes:
        if remove:
            try:
                data["conditions"].pop(barcode)
            except KeyError as e:
                print("Error - Barcode can't be removed, it wasn't in the file.")
        else:
            deplete = dicty["deplete"] == "deplete"
            data["conditions"].update({barcode:{
                    "name": barcode,
                    "control": False,
                    "min_chunks": 0,
                    "max_chunks": 4,
                    "targets": [],
                    "single_on": "unblock" if deplete else "stop_receiving",
                    "single_off": "stop_receiving",
                    "multi_on": "unblock"
                    if deplete
                    else "stop_receiving"
                    if multi_map
                    else "unblock",
                    "multi_off": "stop_receiving",
                    "no_seq": "proceed",
                    "no_map": "proceed",
                }
            })
    write_toml_file(data, toml_path)
