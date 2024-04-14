import json
from py2neo import Graph

CONFIG_ACCOUNT_PATH = 'conf/account.json'


def connect_to_db(db_name):
    with open(CONFIG_ACCOUNT_PATH, 'r') as f:
        data = json.load(f)
        if db_name == 'cryo':
            graph = Graph(data['profile_cryo'], password=data['password_cryo'])
        elif db_name == 'cpa':
            graph = Graph(data['profile_cpa'], password=data['password_cpa'])
    return graph
