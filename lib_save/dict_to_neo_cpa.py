from py2neo import Relationship, Node
import datetime


def dict_to_neo_cpa(graph, dict_body, child):
    cpa_result = create_cpa(graph, dict_body)
    if cpa_result == 'success' or 'exists':
        return create_relation_on_cpa(graph, dict_body, child)
    else:
        return cpa_result

def create_cpa(graph, dict_body):
    try: 
        cpa_node = Node('CPA', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body['Center Node'].items()})
        graph.create(cpa_node)

        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING CPA {dict_body['Center Node']['CPA ID']} \n")
        return 'success'
    
    except Exception as e:
        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} ERROR ON SAVING CPA {dict_body['Center Node']['CPA ID']}: {e} \n")
        if 'already exists' in str(e):
            return 'exists'
        else:
            return 'error'


def create_relation_on_cpa(graph, dict_body, child):
    try:
        cpa_node = graph.nodes.match('CPA', CPA_ID = dict_body['Center Node']["CPA ID"]).first()
        child_node = Node(child, **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body[child].items()})
        graph.create(Relationship(cpa_node, f"{child}_of_CPA", child_node))
        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING {child}_of_CPA {dict_body['Center Node']['CPA ID']} \n")
        return 'success'
    except Exception as e:
        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} ERROR ON SAVING {child}_of_CPA {dict_body['Center Node']['CPA ID']}: {e} \n")
        if 'already exists' in str(e):
            return 'exists'
        else:
            return 'error'