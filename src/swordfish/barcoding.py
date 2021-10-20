import logging
from collections import namedtuple
from itertools import chain, repeat
from pprint import pformat, pprint
from typing import Tuple, Dict, Any, Union, List
import re
from pathlib import Path

import toml
from rich import inspect
from rich.logging import RichHandler
from rich.console import Console

from swordfish.utils import get_barcode_kits, get_device, write_toml_file

formatter = logging.Formatter("[%(asctime)s] - %(message)s", "%Y-%m-%d %H:%M:%S")
handler = RichHandler()
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)
console = Console()


def condition_me(deplete: bool, chunk_str: str) -> dict:
    """
    Return the unclassified and classified conditions for the TOML
    Parameters
    ----------
    deplete: bool
        Is a deplete experiment or not
    chunk_str: str
        / seperated min/max chunk size. ex. 0/4
    Returns
    -------
    dict
        Dictionary of condition
    """
    depletey = "stop_receiving" if deplete else "unblock"
    min_chunk, max_chunk = chunk_str.split("/")
    base_condition = {
        "classified": {
            "name": "classified",
            "control": False,
            "min_chunks": min_chunk,
            "max_chunks": max_chunk,
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
            "min_chunks": min_chunk,
            "max_chunks": max_chunk,
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
        return (
            True
            if barcode_kit in get_barcode_kits(address, names=True)
            or not get_barcode_kits(address)
            else False
        )
    except RuntimeError as e:
        logger.error(repr(e))
        return True


def setup_caller_settings() -> dict:
    """
    Setup Guppy basecaller settings
    Returns
    -------
    dict
        Dict of caller settings
    """
    logger.info("Tell me about your guppy client...\n")
    quests = [
        (
            "address",
            "What is the address it lives at? Mine, for example, lives at localhost. ",
            "localhost",
        ),
        (
            "port",
            "What port should I call at? usually Guppy instances prefer 5555. ",
            "5555",
        ),
    ]
    dicty = {}
    for key, quest, default in quests:
        answer = prompt_user(quest, [console.input], f"Invalid choice", default=default)
        dicty[key] = answer
    return dicty


def prompt_user(
    prompt: str,
    map_func,
    error_msg: str,
    max_tries: int = 3,
    validation_func=None,
    default=None,
) -> [str, Path]:
    """
    prompt_user(prompt, map_func, error_msg, max_tries, validation_func)
    Prompt the user for a setting for the toml
    Parameters
    ----------
    prompt: str
        Question to prompt the user with
    map_func: List of function
        Functions to map in turn to answers, applied in order
    error_msg: Str
        Validation error prompt
    max_tries: int default 3
        The maximum number of tries allowed
    validation_func: function optional
        Validation function
    default: str optional
        Default value to insert if user presses enter
    Returns
    -------
    [str, Path]
        The user input answer
    """
    prompts = chain([f"{prompt}\n"], repeat(f"{error_msg}\n", 3),)
    replies = map(map_func[0], prompts)
    for func in map_func[1:]:
        replies = map(func, replies)
    answer = (
        next(filter(validation_func, replies)) if validation_func else next(replies)
    )
    if not answer and default:
        logger.info(f"You have defaulted to {default}")
        return default
    return answer


def generate_toml_contents_dict(
    is_deplete: bool,
    barcode_string: str,
    reference_file: Path,
    caller_settings_dict: dict,
    barcode_kit: str,
    chunks_str: str,
) -> Tuple[
    Dict[str, Union[Dict[str, str], Dict[str, Union[Union[str, List[str]], Any]]]], dict
]:
    """
    generate_toml_contents_dict(
    is_deplete,
    barcode_string,
    reference_file,
    caller_settings_dict,
    barcode_kit)
    Generate the dictionary to be written into the TOML

    Parameters
    ----------
    is_deplete: bool
        Is a depletion experiment (or not)
    barcode_string: str
        Comma seperated two digit barcode string
    reference_file: Path
        Path to the reference file
    caller_settings_dict: dict
        Address and Host for guppy
    barcode_kit: str
        Barcode kit used in the experiment
    chunks_str: str
        / seperated min/max chunk size. ex. 0/4

    Returns
    -------
    tuple of dict
        Conditions preamble and conditions for each barcode

    """
    min_chunk, max_chunk = chunks_str.split("/")
    toml_body = {
        f"barcode{barcode_number}": {
            "name": f"barcode{barcode_number}",
            "control": False,
            "min_chunks": min_chunk,
            "max_chunks": max_chunk,
            "targets": [],
            "single_on": "unblock" if is_deplete else "stop_receiving",
            "single_off": "unblock" if is_deplete else "stop_receiving",
            "multi_on": "unblock" if is_deplete else "stop_receiving",
            "multi_off": "unblock" if is_deplete else "stop_receiving",
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
    return toml_preamble, toml_body


def overwrite_file(toml_file: Path):
    """
    overwrite_file(toml_file)
    Parameters
    ----------
    toml_file: Path
        File path to toml file
    Returns
    -------
    toml_file: Path
        File path to write to

    """
    overwrite = prompt_user(
        "Overwrite existing toml file? Y/N",
        [input, str.lower],
        "Please type one of Y/N",
        validation_func={"y", "n"}.__contains__,
    )
    do_overwrite = overwrite == "y"
    if not do_overwrite:
        toml_file = prompt_user(
            "Please enter new file name, make sure it ends with .toml!",
            [input, Path],
            "File already exists! Try harder",
            validation_func=Path.exists,
        )
    return toml_file


def barcoding_adventure(args, version) -> None:
    """
    Build your own barcoding adventure! Results not guaranteed
    Returns
    -------
    # TODO max chunks, simple needs to become setup
    None
    """

    toml_path = args.toml
    logger.warning("It's dangerous to go alone, take this TOML file!\n")

    choices = {"deplete", "enrich"}
    type_of_exp = prompt_user(
        "Do you wish to [bold red]deplete[/] or [bold green]enrich[/]?",
        [console.input, str.lower],
        f"Invalid choice, please type one of {'/'.join(choices)}",
        validation_func=choices.__contains__,
    )

    caller_settings_dict = setup_caller_settings()

    pat = re.compile(r"(\d{2},*$)|(\d{2},)+\d{2}$|(\d{2},)+\d{2},$")
    barcode_string = prompt_user(
        f"Comma seperated, two digit barcodes to {type_of_exp} - eg. 02,05,40,20,19 ",
        [console.input],
        "Invalid format, please type barcode digits, comma seperated, no whitespace! ",
        validation_func=pat.fullmatch,
    )
    # todo can't handle multiple inputs
    address = f"{caller_settings_dict['address']}:{caller_settings_dict['port']}"
    barcode_kit = prompt_user(
        "Which mighty barcode kit did you yield?",
        [console.input],
        f"Not in your Guppy Library! One of {get_barcode_kits(address, names=True)}",
        validation_func=lambda reply: validate_barcode_kit(reply, address),
    )
    basecall_config = prompt_user(
        "And which monstrous base calling config devoured your reads? (default on enter dna_r9.4.1_450bps_fast) "
        "- no validation soz",
        [console.input],
        f"",
        default="dna_r9.4.1_450bps_fast",
    )
    # todo user could break everything by putting a lower max chunk than min chunk
    pat = re.compile(r"^(\d/\d)$")
    chunks_string = prompt_user(
        "What is the min/max on your chunk die? Type min/max, i.e 0/4 DO NOT PUT MIN HIGHER THAN MAX",
        [console.input],
        "This format is wrong! I hope you can do better with something like 0/4",
        validation_func=pat.fullmatch,
    )

    logger.info("There's just the question of the reference... Where doth it dwell? ")
    reference_file = prompt_user(
        "Enter a path: ",
        [console.input, Path],
        "This path doesn't exist! Try again: ",
        validation_func=Path.exists,
    )
    is_deplete = True if type_of_exp.lower() == "deplete" else False

    toml_preamble, toml_body = generate_toml_contents_dict(
        is_deplete,
        barcode_string,
        reference_file,
        caller_settings_dict,
        barcode_kit,
        chunks_string,
    )
    classified_body = condition_me(is_deplete, chunks_string)
    classified_body.update(toml_body)
    toml_preamble["conditions"].update(classified_body)
    if toml_path.exists():
        toml_path = overwrite_file(toml_path)
    with open(toml_path, "w") as fh:
        toml.dump(toml_preamble, fh)


def update_barcoding_adventure(args, version):
    """
    Update an existing TOML file ane write out a live file
    Parameters
    ----------
    args: argparse.Namespace
        The arguments provided
    version: str
        The swordfish version
    Returns
    -------
    None

    """
    # todo breaks if nothing in the toml file
    toml_path = args.toml
    logger.info("\nSo you want to update your TOML file.\n")

    with open(toml_path, "r") as fh:
        data = toml.load(fh)
    logger.info("Current barcodes in toml file are...")
    logger.info(
        [
            barcode_name
            for barcode_name in data.get("conditions", {})
            if any(
                [
                    barcode_name.startswith("barcode"),
                    barcode_name in {"classified", "unclassified"},
                ]
            )
        ]
    )

    choices = {"add", "remove"}
    choices_string = f"Please type one of {'/'.join(choices)} " if choices else ""
    type_of_action = prompt_user(
        "Do you want to [bold red]remove[/] or [bold green]add[/] barcode(s) to the TOML file? ",
        [console.input],
        f"Invalid choice. Try again. {choices_string}",
        validation_func=choices.__contains__,
    )
    is_remove = type_of_action == "remove"

    pat = re.compile(r"(\d{2},*$)|(\d{2},)+\d{2}$|(\d{2},)+\d{2},$")
    barcode_string = prompt_user(
        f"Comma seperated, [bold red]two[/] digit barcodes to {type_of_action} - eg. 02,05,40,20,19 ",
        [console.input],
        "Invalid format, please type barcode digits, comma seperated, no whitespace! ",
        validation_func=pat.fullmatch,
    )
    Actions = namedtuple(
        "actions",
        [
            "single_on",
            "single_off",
            "multi_on",
            "multi_off",
            "min_chunks",
            "max_chunks",
        ],
    )
    actions = next(
        (
            Actions(
                value["single_on"],
                value["single_off"],
                value["multi_on"],
                value["multi_off"],
                value["min_chunks"],
                value["max_chunks"],
            )
            for barcode_name, value in data.get("conditions", {}).items()
            if barcode_name.startswith("barcode")
        )
    )

    barcodes = [f"barcode{barcode}" for barcode in barcode_string.split(",")]
    for barcode in barcodes:
        if is_remove:
            try:
                data["conditions"].pop(barcode)
            except KeyError as e:
                logger.error("Error - Barcode can't be removed, it wasn't in the file.")
        else:
            data["conditions"].update(
                {
                    barcode: {
                        "name": barcode,
                        "control": False,
                        "min_chunks": actions.min_chunks,
                        "max_chunks": actions.max_chunks,
                        "targets": [],
                        "single_on": actions.single_on,
                        "single_off": actions.single_off,
                        "multi_on": actions.multi_on,
                        "multi_off": actions.multi_off,
                        "no_seq": "proceed",
                        "no_map": "proceed",
                    }
                }
            )
    write_toml_file(data, toml_path)
