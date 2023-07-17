from py2neo import Relationship, Node
import datetime


def dict_to_neo_cpa(graph, dict_body):
    try:
        ID = dict_body['Center Node']["CPA ID"]
        cpa_node = Node('CPA', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body['Center Node'].items()})
        dsc_node = Node('DSC', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body['DSC'].items()})
        ftir_node = Node('FTIR', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body['FTIR'].items()})
        cryomicro_node = Node('Cryomicroscopy', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body['Cryomicroscopy'].items()})
        osmo_node = Node('Osmolality', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body['Osmolality'].items()})
        visc_node = Node('Viscosity', **{k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in dict_body['Viscosity'].items()})
        # cryomicro_node = Node('Cryomicroscopy')
        # osmo_node = Node('Osmolality')
        # visc_node = Node('Viscosity')

        graph.create(Relationship(cpa_node, "dsc_info_of_cpa", dsc_node))
        graph.create(Relationship(cpa_node, "ftir_info_of_cpa", ftir_node))
        graph.create(Relationship(cpa_node, "cryomicro_info_of_cpa", cryomicro_node))
        graph.create(Relationship(cpa_node, "osmo_info_of_cpa", osmo_node))
        graph.create(Relationship(cpa_node, "visc_info_of_cpa", visc_node))

        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} SUCCESS ON SAVING {ID} \n")
        return 'success'

    except Exception as e:
        with open('log/log_save.txt', 'a+') as file:
            file.write(f"{datetime.datetime.now()} ERROR ON SAVING {ID}: {e} \n")
        if 'already exists' in str(e):
            return 'exists'
        else:
            return 'error'
