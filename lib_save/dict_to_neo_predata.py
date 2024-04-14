import datetime


def dict_to_neo_predata(driver, dict_body):
    with driver.session() as session:
        try:
            ID = dict_body["Sample ID"]
            predata_properties = {k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body.items()}
            session.run(
                "CREATE (predata:PreData $properties)",
                properties=predata_properties
            )

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