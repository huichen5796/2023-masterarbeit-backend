from neo4j import GraphDatabase
import datetime


def dict_to_neo_process(driver, dict_body):
    with driver.session() as session:
        try:
            ID = dict_body["Process ID"]
            process_properties = {k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body.items()}
            session.run(
                "CREATE (process:Process $properties)",
                properties=process_properties
            )

            with open('log/log_save.txt', 'a+') as file:
                file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING PROCESS {ID} \n")
            return 'success'

        except Exception as e:
            if 'already exists' in str(e):
                with open('log/log_save.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} EXISTS ON SAVING PROCESS {ID}: {e} \n")
                return 'exists'
            else:
                with open('log/log_save.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON SAVING PROCESS {ID}: {e} \n")
                return 'error'
