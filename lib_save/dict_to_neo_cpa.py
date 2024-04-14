import datetime


def dict_to_neo_cpa(driver, dict_body, child):
    cpa_result = create_cpa(driver, dict_body)
    if cpa_result == 'success' or 'exists':
        return create_relation_on_cpa(driver, dict_body, child)
    else:
        return cpa_result

def create_cpa(driver, dict_body):
    with driver.session() as session:
        try: 
            cpa_node = {'label': 'CPA', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body['Center Node'].items()}}
            session.run(
                "CREATE (cpa:CPA $properties)",
                properties=cpa_node
            )

            with open('log/log_save.txt', 'a+') as file:
                file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING CPA {dict_body['Center Node']['CPA ID']} \n")
            return 'success'
        
        except Exception as e:
            if 'already exists' in str(e):
                with open('log/log_save.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} EXISTS ON SAVING CPA {dict_body['Center Node']['CPA ID']}: {e} \n")
                return 'exists'
            else:
                with open('log/log_save.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON SAVING CPA {dict_body['Center Node']['CPA ID']}: {e} \n")
                return 'error'


def create_relation_on_cpa(driver, dict_body, child):
    with driver.session() as session:
        try:
            cpa_id = dict_body['Center Node']['CPA ID']
            child_properties = {k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body[child].items()}
            session.run(
                f"MATCH (cpa:CPA {{CPA_ID: $cpa_id}}) "
                f"CREATE (child:{child} $properties) "
                f"CREATE (cpa)-[:{child}_of_CPA]->(child)",
                {"cpa_id": cpa_id, "properties": child_properties}
            )
            with open('log/log_save.txt', 'a+') as file:
                file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING {child}_of_CPA {dict_body['Center Node']['CPA ID']} \n")
            return 'success'
        except Exception as e:
            if 'already exists' in str(e):
                with open('log/log_save.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} EXISTS ON SAVING {child}_of_CPA {dict_body['Center Node']['CPA ID']}: {e} \n")
                return 'exists'
            else:
                with open('log/log_save.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON SAVING {child}_of_CPA {dict_body['Center Node']['CPA ID']}: {e} \n")
                return 'error'