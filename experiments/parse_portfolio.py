import yaml
from lark.lark import Lark
import dolang
from dolang.grammar import parser
from yaml import safe_load
txt  = open("experiments/portfolio.yaml").read()
documents = yaml.load_all(txt, Loader=yaml.SafeLoader)
data = [*documents]

# first kind of model
eqs = (data[0]['equations'])
print(eqs)
e = parser.parse(eqs)

# first kind of model
eqs = (data[1]['equations'])
print(eqs)
e = parser.parse(eqs)
