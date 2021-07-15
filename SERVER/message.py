import json
from dataclasses import dataclass
from dataclasses_json import dataclass_json

from streaming import create_msg


@dataclass_json
@dataclass
class Message:
    shost: str
    dhost: str
    username: str
    date: str
    cont: str
    typ: str
    should_parse_contents: bool = False

    if should_parse_contents:
        if type(cont) == str:
            cont = json.loads(cont)
        else:
            cont = json.dumps(cont)

    def pack(self):
        # parameter is encoded to json. Note that is a string, not a dictionary
        # use aes algorithm to encrypt message if type of massage is not 'iv_exc' or 'key_exc',
        # other wise, send plain text of message
        return create_msg(self.to_json())
