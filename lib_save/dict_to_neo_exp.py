import datetime

def dict_to_neo_probe(driver, dict_body, ExpVer_id):
    with driver.session() as session:
        try:
            ID = dict_body["Sample ID"]
            probe_node = {k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body.items()}
            probe_node['Unique_ID'] = f"{ExpVer_id}*-*{ID}"

            session.run(
                "CREATE (probe:Probe $properties)",
                properties=probe_node
            )
            session.run(
                "MATCH (probe:Probe {Unique_ID: $probe_id}), (versuch:Versuch {Unique_ID: $versuch_id}) "
                "CREATE (probe)-[:probe_of_versuch]->(versuch)",
                probe_id=probe_node['Unique_ID'], versuch_id=ExpVer_id
            )
            for pre_id in dict_body['PreData ID']:
                session.run(
                    "MATCH (probe:Probe {Unique_ID: $probe_id}), (predata:PreData {Sample_ID: $pre_id}) "
                    "CREATE (predata)-[:pre_data_of_probe]->(probe)",
                    probe_id=probe_node['Unique_ID'], pre_id=pre_id
                )
            for post_id in dict_body['PostData ID']:
                session.run(
                    "MATCH (probe:Probe {Unique_ID: $probe_id}), (postdata:PostData {Sample_ID: $post_id}) "
                    "CREATE (postdata)-[:post_data_of_probe]->(probe)",
                    probe_id=probe_node['Unique_ID'], post_id=post_id
                )

            with open(f'log/log_exps/log_{ExpVer_id.split("*-*")[0]}.txt', 'a+') as file:
                file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING PROBE {ID} OF {ExpVer_id} \n")
            return 'success'

        except Exception as e:
            if 'already exists' in str(e):
                with open(f'log/log_exps/log_{ExpVer_id.split("*-*")[0]}.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} EXISTS ON SAVING PROBE {ID} OF {ExpVer_id}: {e} \n")
                return 'exists'
            else:
                with open(f'log/log_exps/log_{ExpVer_id.split("*-*")[0]}.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON SAVING PROBE {ID} OF {ExpVer_id}: {e} \n")
                return 'error'

def dict_to_neo_expriment(driver, dict_body, experiment_id):
    with driver.session() as session:
        try:
            experiment_result = create_experiment_node(session, dict_body, experiment_id)

            infos = []
            for versuch in dict_body:
                if versuch != 'Experiment ID':
                    versuch_properties = {
                        'Versuch_ID': dict_body[versuch]['Versuche ID'],
                        'Unique_ID': f"{experiment_id}*-*{dict_body[versuch]['Versuche ID']}",
                        'F_factor': dict_body[versuch]['F_factor']
                    }
                    session.run(
                        "CREATE (versuch:Versuch $properties)",
                        properties=versuch_properties
                    )

                    session.run(
                        "MATCH (versuch:Versuch {Unique_ID: $versuch_id}), (experiment:Experiment {Experiment_ID: $experiment_id}) "
                        "CREATE (versuch)-[:versuch_of_experiment]->(experiment)",
                        versuch_id=versuch_properties['Unique_ID'], experiment_id=experiment_id
                    )

                    for probe in dict_body[versuch]:
                        if probe not in ['Versuche ID', 'F_factor']:
                            feed_to_neo_result = dict_to_neo_probe(driver, dict_body[versuch][probe], versuch_properties['Unique_ID'])
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
        
def create_experiment_node(session, dict_body, experiment_id):
    try:
        session.run(
            "CREATE (experiment:Experiment {Experiment_ID: $experiment_id})",
            experiment_id=experiment_id
        )
        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} SUCCESS ON CREATE EXPERIMENT {experiment_id} \n")

        with open(f'log/log_exps/log_{experiment_id}.txt', 'w') as file:
                file.write(str(dict_body)+
                    "\nVersuch ID,Sample ID,CPA ID,Process ID,PreData ID,PostData ID,result\n")
        return 'success'
    except Exception as e:
        if 'already exists' in str(e):
            with open(f'log/log_exps/log_{experiment_id}.txt', 'a+') as file:
                file.write(f"{datetime.datetime.now()} EXISTS ON CREATE EXPERIMENT {experiment_id}: {e} \n")
            return 'exists'
        else:
            with open(f'log/log_exps/log_{experiment_id}.txt', 'a+') as file:
                file.write(f"{datetime.datetime.now()} ERROR ON CREATE EXPERIMENT {experiment_id}: {e} \n")
            return 'error'