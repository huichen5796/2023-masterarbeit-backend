
from typing import Any, Dict
import pandas
from scipy.stats import ttest_ind
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from scipy.stats import f_oneway
import ast
import os
import numpy as np
from scipy import stats
from fastapi import FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import json
import urllib.parse
from lib_save import connect_to_db
from lib_build import BuildDatabase, BuildDataStore
from data_to_db import FeedIntoNeo4j
from data_receiver import data_receiver, dict_to_txt
from lib_load import preprocessing_exp_upload

app = FastAPI()

# Allow cross domain requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return 'success'


GRAPH_CRYO = connect_to_db('cryo')
GRAPH_CPA = connect_to_db('cpa')


@app.get("/freeQueryCryo/{query}")
def freeQueryCryo(query):
    query = urllib.parse.unquote(query)
    with GRAPH_CRYO.session() as session:
        return session.run(query).data()


@app.get("/freeQueryCpa/{query}")
def freeQueryCpa(query):
    query = urllib.parse.unquote(query)
    with GRAPH_CPA.session() as session:
        return session.run(query).data()


@app.get("/cleanDatabase/{db_id}")
def cleanDatabase(db_id):
    if db_id == 'cryo':
        BuildDatabase(GRAPH_CRYO, 'cryo').delete_all()
    elif db_id == 'cpa':
        BuildDatabase(GRAPH_CPA, 'cpa').delete_all()
    return f'SUCCESS: DATABASE {db_id} CLEANED'


@app.get("/initDatabase/{db_id}")
def initDatabase(db_id):
    if db_id == 'cryo':
        cleanDatabase('cryo')
        BuildDatabase(GRAPH_CRYO, 'cryo').add_constraint()
    elif db_id == 'cpa':
        cleanDatabase('cpa')
        BuildDatabase(GRAPH_CPA, 'cpa').add_constraint()
    return f'SUCCESS: DATABASE {db_id} INIT'


@app.get("/connectDatabase/{db_id}")
def connectDatabase(db_id):
    if db_id == 'cryo':
        return BuildDatabase(GRAPH_CRYO, 'cryo').query_all()
    elif db_id == 'cpa':
        return BuildDatabase(GRAPH_CPA, 'cpa').query_all()


@app.get("/findIsolatedNodes/{db_id}")
def findIsolatedNodes(db_id):
    if db_id == 'cryo':
        return BuildDatabase(GRAPH_CRYO, 'cryo').find_isolated_nodes()
    elif db_id == 'cpa':
        return BuildDatabase(GRAPH_CPA, 'cpa').find_isolated_nodes()


@app.get("/buildDataStore/{store_name}")
def buildDataStore(store_name):
    return BuildDataStore(store_name).create_data_store_folder()


@app.get("/deleteDataStore/{store_name}")
def deleteDataStore(store_name):
    return BuildDataStore(store_name).delete_folder()


@app.get("/deleteOneType/")
def deleteOneType(store_name, data_type):
    return BuildDataStore(store_name).delete_one_type(data_type)


@app.get("/checkIntegrity/")
def checkIntegrity(store_name, data_type):
    todo = data_type.split(',')
    response = {}
    for file in todo:
        response[file] = BuildDataStore(store_name).create_one_type(file)
    return response


@app.get("/cleanLog/{log_id}")
def cleanLog(log_id):
    try:
        file_path = f'log/{log_id}.txt'
        with open(file_path, 'w') as file:
            file.truncate(0)
        return (f"Cleared file: {file_path}")
    except Exception as e:
        return 'error'


@app.get("/seeLog/{log_id}")
def seeLog(log_id):
    pass


@app.post("/fileUpload/")
async def fileUpload(files: list[UploadFile], data_type, data_store):
    res = []
    if data_type == 'CPA':
        for file in files:
            file_name = "/".join(file.filename.split("/")[-3:])
            upload_result = data_receiver(f'{data_store}/{data_type}/{file_name}', await file.read(), data_type)
            res.append({'file_name': file_name, 'result': upload_result,
                       'neo4j': 'waiting' if upload_result == 'success' else 'undo'})
        return str(res)
    elif data_type == 'ExperimentUpload':
        for file in files:
            upload_result = data_receiver(f'{data_store}/Experiment/{file.filename}', await file.read(), data_type)
            res.append({'file_name': file.filename, 'result': upload_result,
                       'neo4j': 'waiting' if upload_result == 'success' else 'undo'})
        res.append(preprocessing_exp_upload(files, data_store))
        return str(res)
    else:
        for file in files:
            upload_result = data_receiver(f'{data_store}/{data_type}/{file.filename}', await file.read(), data_type)
            res.append({'file_name': file.filename, 'result': upload_result,
                       'neo4j': 'waiting' if upload_result == 'success' else 'undo'})
        return str(res)


@app.post("/fileCreate/")
async def fileCreate(files: list[UploadFile], data_type, data_store):
    res = []
    if data_type == 'CPA':
        for file in files:
            file_name = "/".join(file.filename.split("/")[-3:])
            upload_result = data_receiver(f'{data_store}/{data_type}/{file_name}', dict_to_txt(await file.read(), data_type, file_name), data_type)
            res.append({'file_name': file_name, 'result': upload_result,
                       'neo4j': 'waiting' if upload_result == 'success' else 'undo'})
        return str(res)
    else:
        for file in files:
            upload_result = data_receiver(f'{data_store}/{data_type}/{file.filename}', dict_to_txt(await file.read(), data_type, file.filename), data_type)
            res.append({'file_name': file.filename, 'result': upload_result,
                       'neo4j': 'waiting' if upload_result == 'success' else 'undo'})
        return str(res)


@app.get("/feedInNeo/")
def feedInNeo(data_type, file_name, data_store):
    try:
        if data_type == 'CPA':
            return FeedIntoNeo4j(data_type, f'{data_store}/{data_type}/{file_name}').feed_to_neo4j()
        elif data_type == 'ExperimentCreate':
            return FeedIntoNeo4j(data_type, f'{data_store}/Experiment/{file_name}').feed_to_neo4j()
        elif data_type == 'ExperimentUpload':
            if file_name.split('/')[-1] == 'F.txt':
                return 'success'
            else:
                return FeedIntoNeo4j(data_type, f'{data_store}/Experiment/{file_name}').feed_to_neo4j()
        else:
            return FeedIntoNeo4j(data_type, f'{data_store}/{data_type}/{file_name}').feed_to_neo4j()
    except Exception as e:
        return 'error'


UNIQUE_ID = {
    'PreData': 'Sample_ID',
    'PostData': 'Sample_ID',
    'Experiment': 'Experiment_ID',
    'Probe':'Unique_ID',
    'Versuch':'Unique_ID',
    'Process': 'Process_ID',
    'CPA': 'CPA_ID',
    'DSC': 'DSC_ID',
    'FTIR': 'FTIR_ID',
    'Cryomicroscopy': 'Cryomicroscopy_ID',
    'Osmolality': 'Osmolality_ID',
    'Viscosity': 'Viscosity_ID',
}


@app.get("/queryOneType/")
def queryOneType(data_type):
    query = f"MATCH (p:{data_type}) RETURN COLLECT(p.{UNIQUE_ID[data_type]}) AS idList"
    if data_type in ['PreData', 'PostData', 'Experiment']:
        with GRAPH_CRYO.session() as session:
            result = session.run(query).data()
    else:
        with GRAPH_CPA.session() as session:
            result = session.run(query).data()
    return str(sorted(result[0]['idList'])).replace("'", '"')


@app.get("/queryOneNode/")
def queryOneNode(data_type, ID):
    query = f'MATCH (p:{data_type}) WHERE p.{UNIQUE_ID[data_type]} = "{ID}" RETURN p'
    if data_type in ['PreData', 'PostData', 'Experiment']:
        with GRAPH_CRYO.session() as session:
            result = session.run(query).data()
    else:
        with GRAPH_CPA.session() as session:
            result = session.run(query).data()
    return result[0]['p']


@app.get("/duplicateCheck/")
def duplicateCheck(data_type, ID):
    query = f'MATCH (p:{data_type}) WHERE p.{UNIQUE_ID[data_type]} = "{ID}" RETURN COUNT(p) > 0'
    if data_type in ['PreData', 'PostData', 'Experiment']:
        with GRAPH_CRYO.session() as session:
            result = session.run(query).data()
    else:
        with GRAPH_CPA.session() as session:
            result = session.run(query).data()
    return result[0]["COUNT(p) > 0"]


@app.get("/queryOneExperiment/")
def queryOneExperiment(ID):
    query = f'MATCH(experiment: Experiment)\
              WHERE experiment.Experiment_ID = "{ID}"\
              OPTIONAL MATCH (experiment: Experiment)<-[:versuch_of_experiment]-(second: Versuch)\
              OPTIONAL MATCH (second)<-[:probe_of_versuch*..1]-(third:Probe)\
              WITH experiment, second, COLLECT(DISTINCT third) as thirdNodes\
              RETURN experiment, COLLECT({{versuch: second, probes: thirdNodes}}) as child'
    with GRAPH_CRYO.session() as session:
        result = session.run(query).data()[0]
        result['child'] = sorted(
            result['child'], key=lambda child: child['versuch']['Versuch_ID'])
        for versuch in result['child']:
            versuch['probes'] = sorted(versuch['probes'], key=lambda probe: probe['Sample_ID'])

    return result


@app.get("/queryOneCPA/{ID}")
def queryOneCPA(ID):
    query = f"""MATCH (cpa:CPA {{CPA_ID: '{ID}'}})\
              OPTIONAL MATCH (cpa:CPA {{CPA_ID: '{ID}'}})-[*..1]->(c)\
              WITH cpa, c,\
                CASE labels(c)[0]\
                    WHEN 'DSC' THEN c.DSC_ID\
                    WHEN 'FTIR' THEN c.FTIR_ID\
                    WHEN 'Cryomicroscopy' THEN c.Cryomicroscopy_ID\
                    WHEN 'Osmolality' THEN c.Osmolality_ID\
                    WHEN 'Viscosity' THEN c.Viscosity_ID\
                END AS attribute_value\
              RETURN cpa, COLLECT({{class: labels(c)[0], unique_id:attribute_value, properties: properties(c)}}) AS child"""
    with GRAPH_CPA.session() as session:
        result = session.run(query).data()[0]
    # for child in result['child']:
    #     try:
    #         del child['properties']['Curve']
    #     except:
    #         continue
    return result


@app.post("/queryTheFourElements/")
def queryTheFourElements(data: Dict[Any, Any] = None):
    predata, postdata = data['predata'], data['postdata']
    keys = ['Viability_(%)', 'Total_viable_cells_/_ml_(x_10^6)', 'Average_circularity', 'Average_diameter_(microns)'] # 'Total_viable_cells_/_ml_(x_10^6)'
    results_output = {}
    for index, pre_id in enumerate(predata):
        results_output[pre_id] = {}
    for index, post_id in enumerate(postdata):
        results_output[post_id] = {}
    for key in keys:
        query_pre = f"MATCH (n:PreData)\
                WHERE n.Sample_ID IN {str(predata)}\
                RETURN COLLECT(n.`{key}`) AS data, COLLECT(n.Sample_ID) AS IDs"

        query_post = f"MATCH (n:PostData)\
                WHERE n.Sample_ID IN {str(postdata)}\
                RETURN COLLECT(n.`{key}`) AS data, COLLECT(n.Sample_ID) AS IDs"
        with GRAPH_CRYO.session() as session:
            result_pre = session.run(query_pre).data()[0]
            result_post = session.run(query_post).data()[0]
            results_output[f'average_{key}_pre'] = getMeanAndVariance({'data': result_pre['data']})['mean']
            results_output[f'average_{key}_post'] = getMeanAndVariance({'data': result_post['data']})['mean']
            average_pp = []
            for index, pre_id in enumerate(result_pre['IDs']):
                results_output[pre_id][key] = result_pre['data'][index]
            for index, post_id in enumerate(result_post['IDs']):
                results_output[post_id][key] = result_post['data'][index]
                relativ = f"{(float(result_post['data'][index]) / float(results_output[f'average_{key}_pre'])):.4f}"
                results_output[post_id][f'{key}_relative'] = relativ
                average_pp.append(relativ)
            results_output[f'average_{key}_pp'] = getMeanAndVariance({'data': average_pp})['mean']

    return results_output

@app.post("/getMeanAndVariance/")
def getMeanAndVariance(req: Dict[Any, Any] = None):
    data = req['data']
    # data = urllib.parse.unquote(data)
    # data = ast.literal_eval(data)
    data = [float(item) for item in data]
    mean = np.mean(data)
    variance = np.var(data, ddof=1)
    standard_deviation = np.std(data, ddof=1)
    standard_error = standard_deviation / np.sqrt(len(data))
    confidence_level = 0.95
    n = len(data)
    confidence_interval = stats.t.interval(
        confidence_level, df=n-1, loc=mean, scale=standard_error)

    if n == 1:
        variance = standard_deviation = standard_error = 0.0000
        confidence_interval = (0.00, 0.00)
    q1 = np.percentile(data, 25)  
    median = np.percentile(data, 50)  
    q3 = np.percentile(data, 75) 
    iqr = q3 - q1  
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    low = min([np.round(x,4) for x in data if x >= lower_bound])
    high = max([np.round(x,4) for x in data if x <= upper_bound])

    return {
        "n": f"{n}",
        "mean": f"{mean:.4f}",
        "variance": f"{variance:.4f}",
        "SD": f"{standard_deviation:.4f}",
        "SE": f"{standard_error:.4f}",
        f"CI {confidence_level * 100:.0f}%": [np.round(confidence_interval[0], 4), np.round(confidence_interval[1], 4)],
        'low': f"{low:.4f}",
        'q1': f"{q1:.4f}",
        'median': f"{median:.4f}",
        'q3': f"{q3:.4f}",
        'high': f"{high:.4f}",
        'outliers': [np.round(x,4) for x in data if x < lower_bound or x > upper_bound]
    }


@app.post("/buildColumn/")
def buildColumn(data: Dict[Any, Any] = None):
    
    res = {}
    # predata = urllib.parse.unquote(predata)
    # predata = ast.literal_eval(predata)
    # postdata = urllib.parse.unquote(postdata)
    # postdata = ast.literal_eval(postdata)
    for key, value in data.items():
        res[key] = getMeanAndVariance({'data': [item[0] for item in value]})

    return res


@app.post("/anovaTest/")
def anovaTest(data: Dict[Any, Any] = None):
    # daten = urllib.parse.unquote(daten)
    # daten = ast.literal_eval(daten)
    # # data_dict = ast.literal_eval(data_str)
    # # print(data_dict)
    keys = list(data.keys())
    # data = list(daten.values())
    result = {}

    data_anova = [[float(item[0]) for item in data[key]] for key in keys]

    # ANOVA
    result["F-statistic"], result["p-value"] = f_oneway(*data_anova)

    # Tukey's HSD
    tukey_results = pairwise_tukeyhsd([float(n) for n in np.concatenate(
        data_anova)], np.repeat(keys, [len(d) for d in data_anova]), 0.05)
    df = pandas.DataFrame(
        data=tukey_results._results_table.data[1:], columns=tukey_results._results_table.data[0])
    df['p-adj'] = tukey_results.pvalues
    result["Tukey HSD 0.05"] = list(df.to_dict(orient='index').values())
    result['Tukey Group'] = generate_tukey_subscripts(df)
    return result


def generate_tukey_subscripts(tukey_result_df):

    all_groups = list(set(tukey_result_df["group1"]).union(
        set(tukey_result_df["group2"])))
    gmeans = {}
    gmeans[all_groups[0]] = 0

    related_comparisons = tukey_result_df[(
        tukey_result_df["group1"] == all_groups[0])]
    related_comparisons_2 = tukey_result_df[(
        tukey_result_df["group2"] == all_groups[0])]

    for _, comparison in related_comparisons.iterrows():
        gmeans[comparison["group2"]] = 0 + comparison['meandiff']
    for _, comparison in related_comparisons_2.iterrows():
        gmeans[comparison["group1"]] = 0 - comparison['meandiff']

    sorted_groups = sorted(all_groups, key=lambda group: -gmeans[group])

    result_group = {}
    for group in sorted_groups:
        result_group[group] = ''
    letters = [chr(i) for i in range(ord('a'), ord('z')+1)]
    index = 0

    for i in range(len(sorted_groups)):
        result_group[sorted_groups[i]] += letters[index]
        for j in range(len(sorted_groups)):
            if i != j:
                # p_value = tukey_result_df[(tukey_result_df["group1"] == sorted_groups[i]) & (tukey_result_df["group2"] == sorted_groups[j]) |(tukey_result_df["group2"] == sorted_groups[i]) & (tukey_result_df["group1"] == sorted_groups[j])]['p-adj'].iloc[0]
                p_value = tukey_result_df.loc[
                    ((tukey_result_df["group1"] == sorted_groups[i]) & (tukey_result_df["group2"] == sorted_groups[j])) | (
                        (tukey_result_df["group2"] == sorted_groups[i]) & (tukey_result_df["group1"] == sorted_groups[j])),
                    "p-adj"
                ].iloc[0]
                if p_value >= 0.01:
                    if p_value >= 0.05:
                        result_group[sorted_groups[j]
                                     ] += letters[index]
                    else:
                        result_group[sorted_groups[j]] += letters[index].upper()
        if any(value == '' for value in result_group.values()):
            index += 1
        else:
            break

    return result_group


@app.get("/tTest/")
def tTest(data1, data2, alpha=0.05):
    t_statistic, p_value = ttest_ind(data1, data2)

    is_significant = p_value < alpha

    return {
        "t_statistic": t_statistic,
        "p_value": p_value,
        "is_significant": is_significant
    }


@app.post("/addDelModi/")
def addDelModi(todoSQL: Dict[Any, Any] = None):
    addition, deletion, changeAttr, changeName = todoSQL['addition'], todoSQL['deletion'], todoSQL['changeAttr'], todoSQL['changeName']
    result = {
        'addition': [],
        'deletion': {'nodeAttributes':[], 'childrenNodes': [], 'fatherNodes':[]},
        'changeName': {},
        'changeAttr':{}
    }
    for todo in addition:
        if todo['class'] == 'Versuch':
            driver = GRAPH_CRYO
            try:
                with driver.session() as session:
                    versuch_cypher = """
                    MERGE (versuch:Versuch {Versuch_ID: $Versuch_ID, Unique_ID: $Unique_ID, F_factor: $F_factor})
                    WITH versuch
                    MATCH (experiment:Experiment {Experiment_ID: $Experiment_ID})
                    MERGE (versuch)-[:versuch_of_experiment]->(experiment)
                    RETURN versuch
                    """
                    versuch_params = {
                        "Versuch_ID": todo["info"]["Versuche ID"],
                        "Unique_ID": f'{todo["father"]["Unique_ID"]}*-*{todo["info"]["Versuche ID"]}',
                        "F_factor": todo["info"]["F_factor"],
                        "Experiment_ID": todo['father']['Unique_ID']
                    }
                    session.run(versuch_cypher, versuch_params)
                    create_versuch_result = True
            except:
                create_versuch_result = False
            finally:
                try: 
                    with driver.session() as session:
                        probe_cypher = """
                        MATCH (versuch:Versuch {Unique_ID: $Versuch_Unique_ID})
                        MERGE (probe:Probe {Unique_ID: $Probe_Unique_ID})
                        ON CREATE SET probe += $probe_properties
                        MERGE (probe)-[:probe_of_versuch]->(versuch)
                        """
                        for probe_key in list(todo['info'].keys())[2:]:
                            probe_properties = {k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in todo['info'][probe_key].items()}
                            probe_unique_id = f"{todo['father']['Unique_ID']}*-*{todo['info']['Versuche ID']}*-*{todo['info'][probe_key]['Sample ID']}"
                            session.run(probe_cypher, {"Versuch_Unique_ID": versuch_params["Unique_ID"], "Probe_Unique_ID": probe_unique_id, "probe_properties": probe_properties})
                            
                            for relation_type in ['PreData', 'PostData']:
                                relation_cypher = """
                                MATCH (probe:Probe {Unique_ID: $Probe_Unique_ID})
                                UNWIND $data_ids AS data_id
                                MATCH (data:{relation_type} {Sample_ID: data_id})
                                MERGE (data)-[:{relation_label}]->(probe)
                                """
                                data_ids = todo['info'][probe_key][f'{relation_type} ID']
                                session.run(relation_cypher.format(relation_type=relation_type, relation_label=f'{relation_type.lower()}_of_probe'), {"Probe_Unique_ID": probe_unique_id, "data_ids": data_ids})
                    create_probe_of_versuch = True
                except:
                    create_probe_of_versuch = False
            result['addition'].append('success' if create_versuch_result and create_probe_of_versuch else 'error')
        
        elif todo['class'] == 'Probe':
            driver = GRAPH_CRYO
            try:
                with driver.session() as session:
                    cypher_query = """
                    MATCH (versuch:Versuch {Unique_ID: $versuch_unique_id})
                    MERGE (probe:Probe {Unique_ID: $probe_unique_id})
                    ON CREATE SET probe += $probe_properties
                    MERGE (probe)-[:probe_of_versuch]->(versuch)
                    """

                    probe_properties = {k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in todo['info'].items()}
                    probe_unique_id = f"{todo['father']['Unique_ID']}*-*{todo['info']['Sample ID']}"
                    versuch_unique_id = todo["father"]["Unique_ID"]

                    session.run(cypher_query, {
                        'versuch_unique_id': versuch_unique_id,
                        'probe_unique_id': probe_unique_id,
                        'probe_properties': probe_properties
                    })
                create_rela_pv = True
            except:
                create_rela_pv = False
            try:
                with driver.session() as session:
                    pre_data_cypher = """
                    MATCH (probe:Probe {Unique_ID: $probe_unique_id})
                    UNWIND $pre_ids AS pre_id
                    MATCH (predata:PreData {Sample_ID: pre_id})
                    MERGE (predata)-[:pre_data_of_probe]->(probe)
                    """
                    pre_ids = todo['info']['PreData ID']
                    session.run(pre_data_cypher, {'probe_unique_id': probe_unique_id, 'pre_ids': pre_ids})

                    post_data_cypher = """
                    MATCH (probe:Probe {Unique_ID: $probe_unique_id})
                    UNWIND $post_ids AS post_id
                    MATCH (postdata:PostData {Sample_ID: post_id})
                    MERGE (postdata)-[:post_data_of_probe]->(probe)
                    """
                    post_ids = todo['info']['PostData ID']
                    session.run(post_data_cypher, {'probe_unique_id': probe_unique_id, 'post_ids': post_ids})
                create_rela_ppp = True
            except:
                create_rela_ppp = False
                
            result['addition'].append('success' if create_rela_pv and create_rela_ppp else 'error')

        elif todo['class'] in ['PreData', 'PostData', 'Process']:
            driver = GRAPH_CRYO if todo['class'] != 'Process' else GRAPH_CPA
            with driver.session() as session:
                unique_name = 'Sample_ID' if todo['class'] != 'Process' else 'Process_ID'
                ppp_result = session.run(f"""
                        MATCH (n: {todo['class']})
                        WHERE n.`{unique_name}` = "{todo['unique_id']}"
                        SET n.`{todo['attrKey']}` = "{todo['attrValue']}"
                    """)
                result['addition'].append('success' if check_status_setAndDelete(ppp_result) else 'error')
        else:
            driver = GRAPH_CPA
            if 'father' in list(todo.keys()):
                try:
                    with driver.session() as session:
                        cypher_query = """
                        MATCH (cpa:CPA {CPA_ID: $cpa_id})
                        CREATE (new_node:$class $properties)
                        CREATE (cpa)-[r:$relationship_type]->(new_node)
                        """
                        
                        properties = {k.replace(' ', '_'): str(v) if isinstance(v, dict) else v for k, v in todo['info'].items()}
                        relationship_type = f"{todo['class']}_of_CPA"

                        params = {
                            "cpa_id": todo['father']['Unique_ID'],
                            "class": todo['class'],
                            "properties": properties,
                            "relationship_type": relationship_type
                        }

                        session.run("""
                        CALL apoc.merge.node([$class], {CPA_ID: $cpa_id}, $properties) YIELD node AS new_node
                        MATCH (cpa:CPA {CPA_ID: $cpa_id})
                        CALL apoc.merge.relationship(cpa, $relationship_type, {}, {}, new_node) YIELD rel
                        RETURN new_node, rel
                        """, params)
                    create_node_result = True
                except:
                    create_node_result = False
                result['addition'].append('success' if create_node_result else 'error')
            else:
                with driver.session() as session:
                    result_533 = session.run(f"""
                        MATCH (n: {todo['class']})
                        WHERE n.`{todo['class']}_ID` = "{todo['unique_id']}"
                        SET n.`{todo['attrKey']}` = "{todo['attrValue']}"
                    """)
                    result['addition'].append('success' if check_status_setAndDelete(result_533) else 'error')

    for todo in deletion['nodeAttributes']:
        driver = GRAPH_CRYO if todo['nodeClass'] in ['PreData', 'PostData', 'Versuch', 'Experiment', 'Probe'] else GRAPH_CPA
        with driver.session() as session:
            result_542 = session.run(f"""
                        MATCH (n: {todo['nodeClass']})
                        WHERE n.`{UNIQUE_ID[todo['nodeClass']] if todo['nodeClass'] in list(UNIQUE_ID.keys()) else (todo['nodeClass']+'_ID')}` = "{todo['Unique_ID']}"
                        REMOVE n.`{todo['attributeKey']}`
                    """)
            
            result['deletion']['nodeAttributes'].append('success' if check_status_setAndDelete(result_542) else 'error')
    for todo in deletion['childrenNodes']:
        if todo['nodeClass'] in ['PreData', 'PostData']:
            with GRAPH_CRYO.session() as session:
                result_551 = session.run(f"""
                            MATCH (n: {todo['nodeClass']})
                            WHERE n.Sample_ID = "{todo['Unique_ID']}"
                            OPTIONAL MATCH (n)--(p:Probe)
                            DETACH DELETE n
                            SET p.`{todo['nodeClass']}_ID` = [id IN p.{todo['nodeClass']}_ID WHERE id <> "{todo['Unique_ID']}"]
                        """)
                result['deletion']['childrenNodes'].append('success' if check_status_setAndDelete(result_551) else 'error')
        elif todo['nodeClass'] == 'Process':
            with GRAPH_CPA.session() as session:
                result_560 = session.run(f"""
                            MATCH (n: Process)
                            WHERE n.Process_ID = "{todo['Unique_ID']}"
                            DETACH DELETE n
                        """)
                result['deletion']['childrenNodes'].append('success' if check_status_setAndDelete(result_560) else 'error')
        else:
            with GRAPH_CPA.session() as session:
                result_567 = session.run(f"""
                            MATCH (n: {todo['nodeClass']})
                            WHERE n.`{todo['nodeClass']}_ID` = "{todo['Unique_ID']}"
                            DETACH DELETE n
                        """)
                result['deletion']['childrenNodes'].append('success' if check_status_setAndDelete(result_567) else 'error')

    deletion['fatherNodes'] = sorted(deletion['fatherNodes'], key=custom_sort_key1)
    for todo in deletion['fatherNodes']:
        if todo['nodeClass'] == 'Probe':
            with GRAPH_CRYO.session() as session:
                result_593 = session.run(f"""
                            MATCH (n: Probe)
                            WHERE n.Unique_ID = "{todo['Unique_ID']}"
                            DETACH DELETE n
                        """)
                result['deletion']['fatherNodes'].append('success' if check_status_setAndDelete(result_593) else 'error')
        elif todo['nodeClass'] == 'Experiment':
            with GRAPH_CRYO.session() as session:
                result_584 = session.run(f"""
                            MATCH (e: Experiment)
                            WHERE e.Experiment_ID = "{todo['Unique_ID']}"
                            OPTIONAL MATCH (e)--(v:Versuch)
                            OPTIONAL MATCH (v)--(p:Probe)
                            DETACH DELETE e, v, p
                        """)
                result['deletion']['fatherNodes'].append('success' if check_status_setAndDelete(result_584) else 'error')
        elif todo['nodeClass'] == 'Versuch':
            with GRAPH_CRYO.session() as session:
                result_576 = session.run(f"""
                            MATCH (n: Versuch)
                            WHERE n.Unique_ID = "{todo['Unique_ID']}"
                            OPTIONAL MATCH (n)--(p:Probe)
                            DETACH DELETE n, p
                        """)
                result['deletion']['fatherNodes'].append('success' if check_status_setAndDelete(result_576) else 'error')
        elif todo['nodeClass'] == 'CPA':
            with GRAPH_CPA.session() as session:
                result_600 = session.run(f"""
                            MATCH (c: CPA)
                            WHERE c.CPA_ID = "{todo['Unique_ID']}"
                            OPTIONAL MATCH (c)--(i)
                            DETACH DELETE c, i
                        """)
                result['deletion']['fatherNodes'].append('success' if check_status_setAndDelete(result_600) else 'error')
    
    changeAttr = sorted(changeAttr, key=custom_sort_key)
    for todo in changeAttr:
        driver = GRAPH_CRYO if todo['class'] in ['PreData', 'PostData', 'Versuch', 'Experiment', 'Probe'] else GRAPH_CPA
        if todo['attrKey'] in ['PostData_ID', 'PreData_ID']:
            with driver.session() as session:
                change_attr_pp_probe = session.run(f"""
                        MATCH (p: Probe)
                        WHERE p.Unique_ID = "{todo['unique_id']}"
                        SET p.`{todo['attrKey']}` = {todo['currentValue']}
                    """)
                relation_type = 'pre_data_of_probe' if todo['attrKey']=='PreData_ID' else 'post_data_of_probe'
                delete_rela_pp_probe = session.run(f"""
                        MATCH (p: Probe)-[r:{relation_type}]-()
                        WHERE p.Unique_ID = "{todo['unique_id']}"
                        DELETE r
                    """)
                try:
                    with driver.session() as session:
                        pp_type = 'PreData' if todo['attrKey'] == 'PreData_ID' else 'PostData'
                        relation_type = f"{pp_type.lower()}_of_probe"

                        cypher_query = """
                        MATCH (probe:Probe {Unique_ID: $unique_id})
                        UNWIND $data_ids AS data_id
                        MATCH (pp:$pp_type {Sample_ID: data_id})
                        MERGE (pp)-[:$relation_type]->(probe)
                        """
                        params = {
                            "unique_id": todo['unique_id'],
                            "data_ids": todo['currentValue'],
                            "pp_type": pp_type,
                            "relation_type": relation_type
                        }

                        session.run(cypher_query, params)
                except:
                    change_rela_pp_result = False

                result['changeAttr'][todo['unique_id']+todo['attrKey']] = 'success' if check_status_setAndDelete(change_attr_pp_probe) and check_status_setAndDelete(delete_rela_pp_probe) and change_rela_pp_result else 'error'
        else:
            with driver.session() as session:
                change_attr_result = session.run(f"""
                        MATCH (p: {todo['class']})
                        WHERE p.`{UNIQUE_ID[todo['class']]}` = "{todo['unique_id']}"
                        SET p.`{todo['attrKey']}` = "{todo['currentValue']}"
                    """)
                result['changeAttr'][todo['unique_id']+todo['attrKey']] = 'success' if check_status_setAndDelete(change_attr_result) else 'error'

    changeName = sorted(changeName, key=custom_sort_key)
    for todo in changeName:
        if todo['class'] in ['PreData', 'PostData']:
            with GRAPH_CRYO.session() as session:
                pp_id_result = session.run(f"""
                        MATCH (n:{todo['class']})
                        WHERE n.Sample_ID = "{todo['unique_id']}"
                        OPTIONAL MATCH (n)--(p:Probe)
                        SET n.Sample_ID = "{todo['currentName']}"
                        SET p.`{todo['class']}_ID` = [item IN p.{todo['class']}_ID | CASE WHEN item = "{todo['unique_id']}" THEN "{todo['currentName']}" ELSE item END]
                        """)
                result['changeName'][todo['unique_id']] = 'success' if check_status_setAndDelete(pp_id_result) else 'error'
        
        elif todo['class'] == 'Process':
            with GRAPH_CPA.session() as session:
                change_root_process_result = session.run(f"""
                        MATCH (n:{todo['class']})
                        WHERE n.Process_ID = "{todo['unique_id']}"
                        SET n.Process_ID = "{todo['currentName']}"
                        """)
            with GRAPH_CRYO.session() as session:
                change_cit_process_result = session.run(f"""
                        MATCH (p:Probe)
                        WHERE p.Process_ID = "{todo['unique_id']}"
                        SET p.Process_ID = "{todo['currentName']}"
                        """)
                result['changeName'][todo['unique_id']] = 'success' if check_status_setAndDelete(change_root_process_result) and check_status_setAndDelete(change_cit_process_result) else 'error'

        elif todo['class'] == 'Probe':
            with GRAPH_CRYO.session() as session:
                probe_id_result = session.run(f"""
                        MATCH (p:Probe)
                        WHERE p.Unique_ID = "{todo['unique_id']}"
                        SET p.Sample_ID = "{todo['currentName']}"
                        SET p.Unique_ID = "{todo['unique_id'].rsplit('*-*', 1)[0] + '*-*' + todo['currentName']}"
                        """)
                result['changeName'][todo['unique_id']] = 'success' if check_status_setAndDelete(probe_id_result) else 'error'

        elif todo['class'] == 'Versuch':
            with GRAPH_CRYO.session() as session:
                versuch_id_result = session.run(f"""
                        MATCH (v:Versuch)
                        WHERE v.Unique_ID = "{todo['unique_id']}"
                        SET v.Versuch_ID = "{todo['currentName']}"
                        SET v.Unique_ID = "{todo['unique_id'].rsplit('*-*', 1)[0] + '*-*' + todo['currentName']}"
                        """)
                probe_id_result_v = session.run(f"""
                        MATCH (v:Versuch)--(p:Probe)
                        WHERE v.Unique_ID = "{todo['unique_id'].rsplit('*-*', 1)[0] + '*-*' + todo['currentName']}"
                        WITH p, SPLIT(p.Unique_ID, '*-*') AS parts
                        WITH p, parts[0] + "*-*{todo['currentName']}*-*" + parts[2] AS new_uniqueId
                        SET p.Unique_ID = new_uniqueId
                        """)
                result['changeName'][todo['unique_id']] = 'success' if check_status_setAndDelete(versuch_id_result) and check_status_setAndDelete(probe_id_result_v) else 'error'

        elif todo['class'] == 'Experiment':
            with GRAPH_CRYO.session() as session:
                experiment_id_result = session.run(f"""
                        MATCH (e:Experiment)
                        WHERE e.Experiment_ID = "{todo['unique_id']}"
                        SET e.Experiment_ID = "{todo['currentName']}"
                        """)
                versuch_id_result_e = session.run(f"""
                        MATCH (e:Experiment)--(v:Versuch)
                        WHERE e.Experiment_ID = "{todo['currentName']}"
                        WITH v, SPLIT(v.Unique_ID, '*-*') AS parts
                        WITH v, "{todo['currentName']}*-*" + parts[1] AS new_uniqueIdVersuch
                        SET v.Unique_ID = new_uniqueIdVersuch
                        """)
                probe_id_result_e = session.run(f"""
                        MATCH (e:Experiment)--()--(p:Probe)
                        WHERE e.Experiment_ID = "{todo['currentName']}"
                        WITH p, SPLIT(p.Unique_ID, '*-*') AS partsP
                        WITH p, "{todo['currentName']}*-*" + partsP[1] + "*-*" + partsP[2] AS new_uniqueId
                        SET p.Unique_ID = new_uniqueId
                        """)
                result['changeName'][todo['unique_id']] = 'success' if check_status_setAndDelete(experiment_id_result) and check_status_setAndDelete(versuch_id_result_e) and check_status_setAndDelete(probe_id_result_e) else 'error'
        elif todo['class'] == 'CPA':
            with GRAPH_CPA.session() as session:
                cpa_id_root_result = session.run(f"""
                        MATCH (n:CPA)
                        WHERE n.CPA_ID = "{todo['unique_id']}"
                        SET n.CPA_ID = "{todo['currentName']}"
                        """)
            with GRAPH_CRYO.session() as session:
                cpa_id_cit_result = session.run(f"""
                        MATCH (p:Probe)
                        WHERE p.CPA_ID = "{todo['unique_id']}"
                        SET p.CPA_ID = "{todo['currentName']}"
                        """)
                result['changeName'][todo['unique_id']] = 'success' if check_status_setAndDelete(cpa_id_root_result) and check_status_setAndDelete(cpa_id_cit_result) else 'error'
        else:
            with GRAPH_CPA.session() as session:
                other_id_result = session.run(f"""
                        MATCH (n:{todo['class']})
                        WHERE n.`{todo['class']}_ID` = "{todo['unique_id']}"
                        SET n.`{todo['class']}_ID` = "{todo['currentName']}"
                        """)
                result['changeName'][todo['unique_id']] = 'success' if check_status_setAndDelete(other_id_result) else 'error'

    return result

def check_status_setAndDelete(runResult): 
    summary = runResult.consume()  # This fetches the ResultSummary from the Result object.

    # Accessing the statistics from the summary.
    stats = summary.counters

    # Check various possible changes that indicate success.
    if (stats.properties_set > 0 or stats.relationships_deleted > 0 or stats.nodes_deleted > 0):
        return True  # Return 'success' if any properties were set, or nodes/relationships were deleted.
    
    return False  # Return 'error' if no changes were made.



def custom_sort_key(input_item):
    item = input_item['class']
    if item == 'PreData':
        return (0, item)
    elif item == 'PostData':
        return (1, item)
    elif item == 'Process':
        return (2, item)
    elif item == 'Probe':
        return (4, item)
    elif item == 'Versuch':
        return (5, item)
    elif item == 'Experiment':
        return (6, item)
    elif item == 'CPA':
        return (7, item)
    else:
        return (3, item)
    
def custom_sort_key1(input_item):
    item = input_item['nodeClass']
    if item == 'PreData':
        return (0, item)
    elif item == 'PostData':
        return (1, item)
    elif item == 'Process':
        return (2, item)
    elif item == 'Probe':
        return (4, item)
    elif item == 'Versuch':
        return (5, item)
    elif item == 'Experiment':
        return (6, item)
    elif item == 'CPA':
        return (7, item)
    else:
        return (3, item)