import json
from neo4j import GraphDatabase

CONFIG_ACCOUNT_PATH = 'conf/account.json'


def connect_to_db(db_name):
    with open(CONFIG_ACCOUNT_PATH, 'r') as f:
        data = json.load(f)
        driver = GraphDatabase.driver(data[f'profile_{db_name}'], auth=(data[f'username_{db_name}'], data[f'password_{db_name}']))
    return driver
