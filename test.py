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

