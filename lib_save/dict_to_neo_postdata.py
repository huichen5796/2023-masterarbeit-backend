import datetime


def dict_to_neo_postdata(driver, dict_body):
    with driver.session() as session:
        try:
            ID = dict_body["Sample ID"]
            postdata_properties = {k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body.items()}
            session.run(
                "CREATE (postdata:PostData $properties)",
                properties=postdata_properties
            )

            with open('log/log_save.txt', 'a+') as file:
                file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING POST {ID} \n")
            return 'success'

        except Exception as e:
            if 'already exists' in str(e):
                with open('log/log_save.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} EXISTS ON SAVING POST {ID}: {e} \n")
                return 'exists'
            else:
                with open('log/log_save.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON SAVING POST {ID}: {e} \n")
                return 'error'