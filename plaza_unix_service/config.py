import getpass
import json
import os
import json
import logging
from xdg import XDG_CONFIG_HOME, XDG_DATA_HOME
import threading
import subprocess

from plaza_service import (
    ServiceBlock,
    BlockArgument,
    BlockContext,
    DynamicBlockArgument,
    VariableBlockArgument,
    BlockType,
    VariableClass,
    ServiceTriggerBlock,
)

PLAZA_BRIDGE_ENDPOINT_INDEX = "plaza_bridge_endpoint"
UNIX_SERVICE_CONFIG_PATH_INDEX = "unix_service_configuration_path"

global directory, config_file
directory = os.path.join(XDG_CONFIG_HOME, "plaza", "bridges", "unix")
config_file = os.path.join(directory, "config.json")
pipe_dir = os.path.join(XDG_CONFIG_HOME, "plaza", "bridges", "unix", "pipes")
BUFF_SIZE = 4 << 10  # 4KB

def _get_config():
    if not os.path.exists(config_file):
        return {}
    with open(config_file, "rt") as f:
        return json.load(f)


def _save_config(config):
    os.makedirs(directory, exist_ok=True)
    with open(config_file, "wt") as f:
        return json.dump(config, f, indent=4)


CLASS_TO_TYPE = {
    "string": str
}

class PipeManager(threading.Thread):
    def __init__(self, block, unix_service):
        threading.Thread.__init__(self)
        self.id = block["id"]
        self.unix_service = unix_service

        os.makedirs(pipe_dir, exist_ok=True)
        self.pipe_path = os.path.join(pipe_dir, self.id)
        if not os.path.exists(self.pipe_path):
            os.mkfifo(self.pipe_path)

    def run(self):
        logging.debug("Opening {}".format(self.pipe_path))
        self.reader = open(self.pipe_path, 'rt')
        logging.debug("Opened {}".format(self.pipe_path))
        while True:

            logging.debug("Reading {}".format(self.pipe_path))
            try:
                buff = self.reader.read(BUFF_SIZE)
            except KeyboardInterrupt:
                break

            if len(buff) == 0:
                logging.debug("No more data on {}, waiting for reader"
                             .format(self.pipe_path))
                self.reader = open(self.pipe_path, 'rt')
                continue

            logging.debug("Read [{}]: {}".format(len(buff), buff[:100]))
            self.process(buff)

    def process(self, buff):
        try:
            data = json.loads(buff)
        except:
            data = buff.decode("utf-8")
        self.unix_service.emit_event(self.id, data)

class UnixServiceConfigurationLoader:
    def __init__(self, path):
        self.data = json.load(open(os.path.join(path, 'blocks.json')))
        self.pipe_managers = {}
        self.functions = {}

    async def handle_call(self, function_name, arguments, extra_data):
        return await self.functions[function_name](arguments, extra_data)

    def add_function_definition(self, function_name, block):
        self.functions[function_name] = (lambda args, extra:
                                         self.run_block(block,
                                                        args,
                                                        extra))

    async def run_block(self, block, args, extra):
        command = block["command"]
        if isinstance(command, list):
            params = command + args
        else:
            params = [command] + args
        logging.debug("Running: {}".format(params))
        return subprocess.call(params)

    def get_service_blocks(self):
        blocks = []
        for block in self.data.get("events", []):
            blocks.append(self.create_event(block))

        for block in self.data.get("operations", []):
            blocks.append(self.create_block(block))

        return blocks

    def create_event(self, block_description):
        self.pipe_managers[block_description["id"]] = pipe = PipeManager(
            block_description, self)
        pipe.start()

        return ServiceTriggerBlock(
                    id=block_description["id"],
                    function_name=block_description["id"],
                    message=(block_description["message"].rstrip('. ')
                             + '. Set %1'),
                    arguments=[
                        VariableBlockArgument(),
                    ],
                    save_to=BlockContext.ARGUMENTS[0],
                )

    def create_block(self, block_description):
        block_type = block_description.get('type', 'operation')
        assert block_type == "operation"
        self.add_function_definition(block_description["id"],
                                     block_description)

        return ServiceBlock(
                    id=block_description["id"],
                    function_name=block_description["id"],
                    message=block_description["message"],
                    arguments=[
                        self.create_argument(argument)
                        for argument
                        in block_description.get("arguments", [])
                    ],
                    save_to=None,
                    block_type=BlockType.OPERATION,
                )

    def create_argument(self, argument):
        if argument['type'] == "value":
            return BlockArgument(CLASS_TO_TYPE[argument['class']],
                                 argument['title'])

    def emit_event(self, id, data):
        raise NotImplementedError("This method must be overriden by the service using this configuration")

def get_default_configuration():
    config = _get_config()
    if config.get(UNIX_SERVICE_CONFIG_PATH_INDEX, None) is None:
        config[UNIX_SERVICE_CONFIG_PATH_INDEX] = conf_dir = os.path.join(
            XDG_DATA_HOME, "plaza", "bridges", "unix")

        os.makedirs(conf_dir, exist_ok=True)
        blocks_file = os.path.join(conf_dir, 'blocks.json')
        if not os.path.exists(blocks_file):
            with open(blocks_file, 'wt') as f:
                json.dump({ 'operations': [], 'events': [] }, f, indent=4)
            logging.info("Created block definition file at: {}".format(
                blocks_file
            ))

        _save_config(config)
    return UnixServiceConfigurationLoader(config[UNIX_SERVICE_CONFIG_PATH_INDEX])


def get_bridge_endpoint():
    config = _get_config()
    if config.get(PLAZA_BRIDGE_ENDPOINT_INDEX, None) is None:
        config[PLAZA_BRIDGE_ENDPOINT_INDEX] = input("Plaza bridge endpoint: ")
        if not config[PLAZA_BRIDGE_ENDPOINT_INDEX]:
            raise Exception("No bridge endpoint introduced")
        _save_config(config)
    return config[PLAZA_BRIDGE_ENDPOINT_INDEX]
