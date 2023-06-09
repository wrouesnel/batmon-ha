import json
import os.path
import re
from os import R_OK, access
from os.path import isfile, join
from threading import Lock
from typing import Optional, Sequence

from batmon.bmslib.util import dotdict, get_logger

logger = get_logger()

lock = Lock()

BMS_METER_STATES_FILENAME = "bms_meter_states.json"

root_dir: Optional[str] = None
bms_meter_states: Optional[str] = None

def set_data_dir(path: str):
    global root_dir
    global bms_meter_states

    if not os.path.isdir(path):
        raise Exception(f"Path supplied is not a directory: {path}")
    if not os.access(path, os.W_OK):
        raise Exception(f"Supplied directory is not writable: {path}")

    with lock:
        root_dir = path
        bms_meter_states = os.path.join(root_dir, BMS_METER_STATES_FILENAME)

def store_file(filename: str) -> str:
    if root_dir is None:
        raise Exception("store has not been initialized")
    return os.path.join(root_dir, filename)

def load_meter_states():
    with lock:
        with open(bms_meter_states) as f:
            meter_states = json.load(f)
        return meter_states


def store_meter_states(meter_states):
    with lock:
        with open(bms_meter_states, "w") as f:
            json.dump(meter_states, f)


def store_algorithm_state(bms_name, algorithm_name, state=None):
    fn = root_dir + "bat_state_" + re.sub(r"[^\w_. -]", "_", bms_name) + ".json"
    with lock:
        with open(fn, "a+") as f:
            try:
                f.seek(0)
                bms_state = json.load(f)
            except:
                logger.info("init %s bms state storage", bms_name)
                bms_state = dict(algorithm_state=dict())

            if state is not None:
                bms_state["algorithm_state"][algorithm_name] = state
                f.seek(0), f.truncate()
                json.dump(bms_state, f)

            return bms_state["algorithm_state"].get(algorithm_name, None)


def load_user_config(config_path: Optional[str]):
    conf = None
    if config_path is None:
        try:
            with open("/data/options.json", "rt") as f:
                conf = dotdict(json.load(f))
                _user_config_migrate_addresses(conf)
        except Exception as e:
            logger.info(f"Error reading config path - trying options.json")
            with open("options.json", "rt") as f:
                conf = dotdict(json.load(f))
    else:
        try:
            with open(config_path, "rt") as f:
                conf = dotdict(json.load(f))
        except Exception as e:
            logger.error(f"Error reading config path: {config_path}")

    if conf is None:
        raise Exception("Could not load any configuration file")
    return conf


def _user_config_migrate_addresses(conf):
    changed = False
    slugs = ["daly", "jbd", "jk", "victron"]
    conf["devices"] = conf.get("devices") or []
    devices_by_address = {d["address"]: d for d in conf["devices"]}
    for slug in slugs:
        addr = conf.get(f"{slug}_address")
        if addr and not devices_by_address.get(addr):
            device = dict(
                address=addr.strip("?"),
                type=slug,
                alias=slug + "_bms",
            )
            if addr.endswith("?"):
                device["debug"] = True
            if conf.get(f"{slug}_pin"):
                device["pin"] = conf.get(f"{slug}_pin")
            conf["devices"].append(device)
            del conf[f"{slug}_address"]
            logger.info("Migrated %s_address to device %s", slug, device)
            changed = True
    if changed:
        logger.info("Please update add-on configuration manually.")
