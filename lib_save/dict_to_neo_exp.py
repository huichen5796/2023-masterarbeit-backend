import datetime
from py2neo import Node, Relationship
import os

def dict_to_neo_probe(graph, dict_body, ExpVer_id):
    try:
        ID = dict_body["Sample ID"]
        probe_node = Node('Probe',**{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body.items()}, Unique_ID=f"{ExpVer_id}*-*{dict_body['Sample ID']}")

        versuch_node = graph.nodes.match('Versuch', Unique_ID = ExpVer_id).first()
        graph.create(Relationship(probe_node, 'probe_of_versuch', versuch_node))
        for pre_id in dict_body['PreData ID']:
            predata_node = graph.nodes.match('PreData', Sample_ID = pre_id).first()
            graph.create(Relationship(predata_node, 'pre_data_of_probe', probe_node))
        for post_id in dict_body['PostData ID']:
            postdata_node = graph.nodes.match('PostData', Sample_ID = post_id).first()
            graph.create(Relationship(postdata_node, 'post_data_of_probe', probe_node))

        with open(f'log/log_exps/log_{ExpVer_id.split("*-*")[0]}.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING PROBE {ID} OF {ExpVer_id} \n")
        return 'success'

    except Exception as e:
        with open(f'log/log_exps/log_{ExpVer_id.split("*-*")[0]}.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} ERROR ON SAVING PROBE {ID} OF {ExpVer_id}: {e} \n")
        if 'already exists' in str(e):
            return 'exists'
        else:
            return 'error'

def dict_to_neo_expriment(graph, dict_body, experiment_id):
    try:
        experiment_result = create_experiment_node(graph, dict_body, experiment_id)

        infos = []
        for versuch in dict_body:
            if versuch !='Experiment ID':
                versuch_node = Node('Versuch',Versuch_ID = dict_body[versuch]['Versuche ID'], Unique_ID = f"{experiment_id}*-*{dict_body[versuch]['Versuche ID']}", F_factor = dict_body[versuch]['F_factor'])
                
                experiment_node = graph.nodes.match('Experiment', Experiment_ID = experiment_id).first()
                graph.create(Relationship(versuch_node, 'versuch_of_experiment', experiment_node))

                for probe in dict_body[versuch]:
                    if probe == 'Versuche ID':
                        continue
                    elif probe == 'F_factor':
                        continue
                    else:
                        with open(f'log/log_exps/log_{experiment_id}.txt', 'a+') as file:
                            file.write(
                                f"{datetime.datetime.now()} SUCCESS ON LOADING PROBE DATA: {dict_body[versuch][probe]['Sample ID']} OF {experiment_id}*-*{dict_body[versuch]['Versuche ID']} \n")
                        
                        feed_to_neo_result = dict_to_neo_probe(graph, dict_body[versuch][probe], f"{experiment_id}*-*{dict_body[versuch]['Versuche ID']}")
                        with open(f'log/log_exps/log_{experiment_id}.txt', 'a+') as file:
                            file.write(
                                f"{versuch},{dict_body[versuch][probe]['Sample ID']},{dict_body[versuch][probe]['CPA ID']},{dict_body[versuch][probe]['Process ID']},{dict_body[versuch][probe]['PreData ID']},{dict_body[versuch][probe]['PostData ID']},{feed_to_neo_result} \n")

                        infos.append(feed_to_neo_result)
        
        if all(element == 'success' for element in infos):
            return 'success'
        else:
            return 'see-error-detail'

    except Exception as e:
       with open(f'log/log_exps/log_{experiment_id}.txt', 'a+') as file:
           file.write(
               f"{datetime.datetime.now()} ERROR ON SAVING versuch OF EXP: {experiment_id}: {e} \n")
    
       return 'error'
    
def create_experiment_node(graph, dict_body, experiment_id):
    try:
        experiment_node = Node('Experiment',Experiment_ID = experiment_id)
        graph.create(experiment_node)
        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} SUCCESS ON CREATE EXPERIMENT {experiment_id} \n")

        with open(f'log/log_exps/log_{experiment_id}.txt', 'w') as file:
                file.write(str(dict_body)+
                    "\nVersuch ID,Sample ID,CPA ID,Process ID,PreData ID,PostData ID,result\n")
        return 'success'
    except Exception as e:
        if 'already exists' in str(e):
            return 'exists'
        else:
            with open(f'log/log_exps/log_{experiment_id}.txt', 'a+') as file:
                file.write(f"{datetime.datetime.now()} ERROR ON CREATE EXPERIMENT {experiment_id}: {e} \n")
            return 'error'