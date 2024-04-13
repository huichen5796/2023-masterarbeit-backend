import datetime


class BuildDatabase:
    def __init__(self, driver, db_id):
        self.driver = driver
        self.db_id = db_id
    
    def delete_all(self):
        with self.driver.session() as session:
            try:
                session.run("MATCH (n) DETACH DELETE n")
                constraints_query = "SHOW CONSTRAINTS"
                constraint_records = session.run(constraints_query).data()
                unique_constraint_names = [record['name'] for record in constraint_records if record['type'] == 'UNIQUENESS']
                for constraint_name in unique_constraint_names:
                    drop_constraint_query = f"DROP CONSTRAINT {constraint_name}"
                    session.run(drop_constraint_query)

                with open('log/log_build.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} SUCCESS ON DELETE ALL: {self.db_id} \n")
            except Exception as e:
                with open('log/log_build.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON DELETE ALL: {self.db_id}: {e} \n")


    def add_constraint(self):
        with self.driver.session() as session:
            try:
                if self.db_id == 'cryo':
                    constraints = [
                        ("PreData", "Sample_ID"),
                        ("PostData", "Sample_ID"),
                        ("Experiment", "Experiment_ID"),
                        ("Probe", "Unique_ID"),
                        ("Versuch", "Unique_ID")
                    ]
                elif self.db_id == 'cpa':
                    constraints = [
                        ("CPA", "CPA_ID"),
                        ("Process", "Process_ID"),
                        ("DSC", "DSC_ID"),
                        ("FTIR", "FTIR_ID"),
                        ("Cryomicroscopy", "Cryomicroscopy_ID"),
                        ("Osmolality", "Osmolality_ID"),
                        ("Viscosity", "Viscosity_ID")
                    ]

                for node, id_field in constraints:
                    session.run(f"CREATE CONSTRAINT ON (n:{node}) ASSERT n.{id_field} IS UNIQUE")

                with open('log/log_build.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} SUCCESS ON ADD CONSTRAINT: {self.db_id} \n")
            except Exception as e:
                with open('log/log_build.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON ADD CONSTRAINT: {self.db_id}: {e} \n")
    
    def query_all(self):
        with self.driver.session() as session:
            try:
                node_counts = session.run("MATCH (n) RETURN DISTINCT labels(n) AS label, count(*) AS count").data()
                relationship_counts = session.run("MATCH ()-[r]->() RETURN DISTINCT type(r) AS type, count(*) AS count").data()
                
                rep = {"Node": {}, "Relation": {}}
                for result in node_counts:
                    label = result['label'][0]  # Assumes each node has exactly one label
                    count = result['count']
                    rep['Node'][f'{label} node'] = count

                for result in relationship_counts:
                    relationship_type = result['type']
                    count = result['count']
                    rep['Relation'][f'{relationship_type}'] = count

                with open('log/log_build.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} SUCCESS ON QUERY ALL: {self.db_id} \n")
                return str(rep)
                
            except Exception as e:
                with open('log/log_build.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON QUERY ALL: {self.db_id}: {e} \n")
                return 'error'
    
    def find_isolated_nodes(self):
        with self.driver.session() as session:
            try:
                result = session.run('MATCH (n) WHERE NOT (n)--() RETURN n.Sample_ID as Sample_ID').data()
                isolated_nodes = [record['Sample_ID'] for record in result if 'Sample_ID' in record]

                with open('log/log_build.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} SUCCESS ON FIND ISOLATED NODES: {self.db_id} \n")
                return str(isolated_nodes)

            except Exception as e:
                with open('log/log_build.txt', 'a+') as file:
                    file.write(f"{datetime.datetime.now()} ERROR ON FIND ISOLATED NODES: {self.db_id}: {e} \n")
                return 'error'
