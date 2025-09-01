# monkey-patch yaml so that yaml.compose becomes more usable.
import yaml
from yaml import MappingNode, SequenceNode, ScalarNode
from typing import Union

MappingNode.keys = lambda self: [e[0].value for e in self.value]
MappingNode.values = lambda self: [e[1] for e in self.value]
MappingNode.items = lambda self: iter([(e[0].value, e[1]) for e in self.value])
MappingNode.__getitem__ = lambda self, key: self.value[self.keys().index(key)][1]
MappingNode.__iter__ = lambda self: iter(self.keys())


def __mn__get__(self, key, default=None):
    if key in self.keys():
        return self[key]
    else:
        return default


MappingNode.get = __mn__get__


def __mn__setitem__(self, key: str, value: Union[str, float, int]):
    assert isinstance(key, str)
    if isinstance(value, str):
        new_value = ScalarNode(tag="tag:yaml.org,2002:str", value=value)
    elif isinstance(value, int):
        new_value = ScalarNode(tag="tag:yaml.org,2002:int", value=value)
    elif isinstance(value, float):
        new_value = ScalarNode(tag="tag:yaml.org,2002:float", value=value)
    else:
        raise Exception(f"Unknown type for {value}")
    if key not in self.keys():
        new_key = ScalarNode(tag="tag:yaml.org,2002:str", value="name")
        self.value.append((new_key, new_value))
    else:
        i = self.keys().index(key)
        k = self.value[i][0]
        self.value[i] = (k, new_value)


MappingNode.__setitem__ = __mn__setitem__

MappingNode.__getitem__ = lambda self, key: self.value[self.keys().index(key)][1]

MappingNode.__contains__ = lambda self, key: (key in self.keys())
MappingNode.__len__ = lambda self: len(self.value)


def __mn_update__(self, kw):
    for k, w in kw.items():
        self[k] = w


MappingNode.update = __mn_update__

SequenceNode.__getitem__ = lambda self, i: self.value[i]
SequenceNode.__len__ = lambda self: len(self.value)
SequenceNode.__iter__ = lambda self: iter(self.value)
