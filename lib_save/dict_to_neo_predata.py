from py2neo import Node
import datetime


def dict_to_neo_predata(graph, dict_body):
    try:
        ID = dict_body["Sample ID"]
        
        process_node = Node('PreData', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body.items()})
        graph.create(process_node)

        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING PRE {ID} \n")
        return 'success'

    except Exception as e:
        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} ERROR ON SAVING PRE {ID}: {e} \n")
        if 'already exists' in str(e):
            return 'exists'
        else:
            return 'error'