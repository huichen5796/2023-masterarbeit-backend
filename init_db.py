class Check:
    def __init__(self, graph, db_id):
        self.graph = graph
        self.db_id = db_id
    
    def delete_all(self):
        self.graph.delete_all()

        constraints_query = "SHOW CONSTRAINTS"
        constraint_records = self.graph.run(constraints_query).data()
        unique_constraint_names = [record['name'] for record in constraint_records if record['type'] == 'UNIQUENESS']
        for constraint_name in unique_constraint_names:
            drop_constraint_query = f"DROP CONSTRAINT {constraint_name}"
            self.graph.run(drop_constraint_query)


    def add_constraint(self):
        if self.db_id == 'cryo':
            self.graph.run(f'CREATE CONSTRAINT FOR (n: PreData) REQUIRE n.Sample_ID IS UNIQUE')
            self.graph.run(f'CREATE CONSTRAINT FOR (n: PostData) REQUIRE n.Sample_ID IS UNIQUE')
            self.graph.run(f'CREATE CONSTRAINT FOR (n: Experiment) REQUIRE n.Experiment_ID IS UNIQUE')
        elif self.db_id == 'cpa':
            self.graph.run(f'CREATE CONSTRAINT FOR (n: CPA) REQUIRE n.CPA_ID IS UNIQUE')
            self.graph.run(f'CREATE CONSTRAINT FOR (n: Process) REQUIRE n.Process_ID IS UNIQUE')
            self.graph.run(f'CREATE CONSTRAINT FOR (n: DSC) REQUIRE n.File_ID IS UNIQUE')
            self.graph.run(f'CREATE CONSTRAINT FOR (n: FTIR) REQUIRE n.File_ID IS UNIQUE')
            # self.graph.run(f'CREATE CONSTRAINT FOR (n: Cryomicroscopy) REQUIRE n.File_ID IS UNIQUE')
            # self.graph.run(f'CREATE CONSTRAINT FOR (n: Osmolality) REQUIRE n.File_ID IS UNIQUE')
            # self.graph.run(f'CREATE CONSTRAINT FOR (n: Viscosity) REQUIRE n.File_ID IS UNIQUE')
    
    def query_all(self):
        rep = {
            "Node": {},
            "Relation": {}
        }
        node_counts = self.graph.run("MATCH (n) RETURN DISTINCT labels(n) AS label, count(*) AS count").data()
        for result in node_counts:
            label = result['label'][0]
            count = result['count']
            rep['Node'][f'{label} node'] = count

        relationship_counts = self.graph.run("MATCH ()-[r]->() RETURN DISTINCT type(r) AS type, count(*) AS count").data()
        for result in relationship_counts:
            relationship_type = result['type']
            count = result['count']
            rep['Relation'][f'{relationship_type} node'] = count
        return str(rep)
    
    def find_isolated_nodes(self):
        result = self.graph.run('MATCH (n) WHERE NOT (n)--() RETURN n.Sample_ID as Sample_ID').data()
        isolated_nodes = [record['Sample_ID'] for record in result]
        return str(isolated_nodes)