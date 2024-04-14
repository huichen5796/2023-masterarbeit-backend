from scipy.stats import ttest_ind
import random
from data_to_db import FeedIntoNeo4j
from main import *

cleanLog('log_build')
cleanLog('log_load')
cleanLog('log_save')
cleanLog('log_upload')

deleteDataStore('data_store')
buildDataStore('data_store')

cleanDatabase('cpa')
initDatabase('cpa')
cleanDatabase('cryo')
initDatabase('cryo')


# print(FeedIntoNeo4j('predata', 'data_store\pre_data\EQ20220824A1-Pre1.txt').feed_to_neo4j())
# print(FeedIntoNeo4j('postdata', 'data_store\post_data\EQ20220824-3c-LN2-4-4.txt').feed_to_neo4j())
# print(FeedIntoNeo4j('exp', 'data_store\exp\experiment_1.txt').feed_to_neo4j())

# print(FeedIntoNeo4j('cpa', 'data_store\cpa\CPA1').feed_to_neo4j())
# print(FeedIntoNeo4j('process', 'data_store\process\Prozess1.txt').feed_to_neo4j())

# import numpy as np
# from scipy.stats import f_oneway
# from statsmodels.stats.multicomp import pairwise_tukeyhsd


# def perform_anova(daten):
#     keys = list(daten.keys())
#     data = list(daten.values())

#     result = {}

#     # ANOVA
#     f_statistic, p_value = f_oneway(*data)

#     result["F-statistic"] = f_statistic
#     result["p-value"] = p_value

#     # Tukey's HSD
#     tukey_results = pairwise_tukeyhsd(np.concatenate(
#         data), np.repeat(keys, [len(d) for d in data]), 0.05)
#     print()
#     df = pandas.DataFrame(
#         data=tukey_results._results_table.data[1:], columns=tukey_results._results_table.data[0])
#     df['p-adj'] = tukey_results.pvalues
#     result["Tukey HSD"] = tukey_results

#     return result


# daten = {
#     'data_A': np.random.normal(np.random.uniform(0, 10), np.random.uniform(1, 3), 10),
#     'data_B': np.random.normal(np.random.uniform(0, 10), np.random.uniform(1, 3), 10),
#     'data_C': np.random.normal(np.random.uniform(0, 10), np.random.uniform(1, 3), 10)
# }

# result = perform_anova(daten)
# print(result['Tukey HSD'])
# print(result)

# def independent_ttest(data1, data2, alpha=0.05):
#     t_statistic, p_value = ttest_ind(data1, data2)

#     is_significant = p_value < alpha

#     return t_statistic, p_value, is_significant

# print(independent_ttest(daten['data_A'], daten['data_B']))

# def generate_tukey_subscripts(tukey_result_df):

#     all_groups = list(set(tukey_result_df["group1"]).union(
#         set(tukey_result_df["group2"])))
#     gmeans = {}
#     gmeans[all_groups[0]] = 0

#     related_comparisons = tukey_result_df[(
#         tukey_result_df["group1"] == all_groups[0])]
#     related_comparisons_2 = tukey_result_df[(
#         tukey_result_df["group2"] == all_groups[0])]

#     for _, comparison in related_comparisons.iterrows():
#         gmeans[comparison["group2"]] = 0 + comparison['meandiff']
#     for _, comparison in related_comparisons_2.iterrows():
#         gmeans[comparison["group1"]] = 0 - comparison['meandiff']

#     sorted_groups = sorted(all_groups, key=lambda group: -gmeans[group])

#     print(sorted_groups)

#     result_group = {}
#     for group in sorted_groups:
#         result_group[group] = ''
#     letters = [chr(i) for i in range(ord('a'), ord('z')+1)]
#     index = 0

#     for i in range(len(sorted_groups)):
#         result_group[sorted_groups[i]] += letters[index]
#         for j in range(len(sorted_groups)):
#             if i != j:
#                 # p_value = tukey_result_df[(tukey_result_df["group1"] == sorted_groups[i]) & (tukey_result_df["group2"] == sorted_groups[j]) |(tukey_result_df["group2"] == sorted_groups[i]) & (tukey_result_df["group1"] == sorted_groups[j])]['p-adj'].iloc[0]
#                 p_value = tukey_result_df.loc[
#                     ((tukey_result_df["group1"]==sorted_groups[i]) & (tukey_result_df["group2"]==sorted_groups[j])) | ((tukey_result_df["group2"]==sorted_groups[i]) & (tukey_result_df["group1"]==sorted_groups[j])),
#                     "p-adj"
#                 ].iloc[0]
#                 if p_value <= 0.05:
#                     if p_value <= 0.01:
#                         print(sorted_groups[i], sorted_groups[j])
#                         result_group[sorted_groups[j]] += letters[index].upper()
#                         print(result_group)
#                     else:
#                         print(sorted_groups[i], sorted_groups[j])
#                         result_group[sorted_groups[j]] += letters[index]
#                         print(result_group)
#         if any(value == '' for value in result_group.values()):
#             index += 1
#         else:
#             break


#     return result_group


# tukey_result_df = df = pandas.DataFrame(
#     data=result['Tukey HSD']._results_table.data[1:], columns=result['Tukey HSD']._results_table.data[0])

# subscripts_df = generate_tukey_subscripts(tukey_result_df)
# print(subscripts_df)


# def check_status_setAndDelete(runResult): 
#     # stats = runResult.stats()

#     if (runResult.get('relationships_deleted', 0) or runResult.get('properties_set', 0) or runResult.get('nodes_deleted', 0)):
#         return True #'success'
    
#     return False # 'error'


# dict1 = {"relationships_deleted":0}
# dict2 = {"relationships_deleted":1}
# dict3 = {"relationships_deleted":5}
# dict4 = {}
# dict5 = {"properties_set":0}
# dict6 = {"properties_set":'0'}
# dict7 = {"dasda":0}
# dict8 = {'nodes_deleted': 0, 'relationships_deleted': 4, 'properties_set': 4}
# for i in [dict1, dict2, dict3, dict4, dict5, dict6, dict7, dict8]:
#     print(check_status_setAndDelete(i))