#import libraries
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import argparse
import yaml
import json
from datetime import date

#Setup arguments for argparse to allow input of ds, doi and filepaths in terminal
parser = argparse.ArgumentParser(description='Accepts paper DOI and ds name and pathnames to datafiles (see args). Returns a tsv file with "filename", "label", "AD:construct", "DBD:construct" and "part_of" for entry into the VFB curation interface.')
parser.add_argument('--doi', '-doi', type=str, help='A string referring to the DOI, use "|" to merge results from multiple DOIs')
parser.add_argument('--year', '-y', type=str, help='A string to be appended to the filename to indicate data batch')
parser.add_argument('--ds', '-ds', type=str, help='A string to name the dataset (omit split_)')
parser.add_argument('--janelia_json', '-f', type=str, help='path to most recent janelia json')
parser.add_argument('--splits', '-s', type=str, help='path to flylight_combination_lines_2.tsv')
parser.add_argument('--stochastic_effectors', '-stoch', type=str, help='path to stochastic_effectors_list_01_2021.tsv')
parser.add_argument('--curator', '-c', type=str, help='curator name, must be in KB')
parser.add_argument('--effectors', '-e', type=str, help='path to Reporter_Codes_with_FB_Mapping_current_IDs.csv')
args = vars(parser.parse_args())

##args for testing in ide (should be commented out)
# doi = '10.1002/cne.24512'
# ds = 'Wolff2018'
# year = '2018'
# janelia_json = '/Users/alexmclachlan/Downloads/janelia_2020_12_15.json'
# splits = '/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/resources/flylight_combination_lines_2.tsv'
# stochastic_effectors = '/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/resources/stochastic_effectors_list_01_2021.tsv'
# curator = 'adm71'
# effectors = '/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/resources/Reporter_Codes_with_FB_Mapping_current_IDs copy.csv'

#asign args to variables
doi = args['doi']
ds = args['ds']
year = args['year']
janelia_json = args['janelia_json']
splits = args['splits']
stochastic_effectors = args['stochastic_effectors']
curator = args['curator']
effectors = args['effectors']

##create yaml data and write file
#yaml data
yaml_data = dict(
    DataSet=ds,
    Imaging_type='confocal microscopy',
    Curator=curator)
#write yaml file
with open('/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/curation_tsvs/split_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.yaml', 'w') as outfile:
    yaml.dump(yaml_data, outfile, default_flow_style=False)

##get all relevant data from janelia .json
#extract only rows with appropriate doi
with open(janelia_json) as f:
   current_data = json.load(f)

janelia_df=pd.DataFrame(current_data['images'])

#extract only rows with appropriate doi
janelia_df = janelia_df[janelia_df['doi'].str.contains(doi, na=False)].reset_index()

#extract relevant columns
names_ext = janelia_df[['publishing_name', 'ad', 'dbd', 'gender', 'area', 'slide_code', 'objective', 'sampleId', 'tile', 'age', 'published_externally', 'effector', 'line', 'objectiveName', 'mounting_protocol']]

#remove rows where 'published_externally' does not = 1 (confirmed working as values are either '1' or None)
names_ext = names_ext[names_ext['published_externally'].str.contains('1', na=False)]

#add effector genotypes from gillian csv
effector_genotypes=pd.read_csv(effectors)
names_ext=names_ext.merge(effector_genotypes, how='left', left_on='effector', right_on='Reporter Code')

##remove stochastic effectors.
#load stochastic_effectors tsv file to df
stochastic_effectors=pd.read_csv(stochastic_effectors, sep='\t', index_col=False)
#drop rows with effectors matching any of the stochastic_effectors
names_ext=names_ext[~names_ext['effector'].str.contains('|'.join(list(stochastic_effectors['Effector'])))]

#fillna in 'tile'
names_ext['tile']=names_ext['tile'].fillna('null')

##add label
#add info from fields to label
names_ext['label']= 'JRC_' + names_ext['publishing_name'] + '_' + names_ext['area'] + '_' + year +'_' + names_ext['slide_code'] + '_' + names_ext['objective']
#fill filename column with 'objective-area-sampleid'
names_ext['filename']=names_ext['objective'] + '-' + names_ext['area'] + '-' +  names_ext['sampleId']


##extract unique brains, taking 20x and 63x when ALL of left_dorsal, ventral, right_dorsal tiles exist
#split out brain TODO report if any images are 40x
#get 20x images
names_ext_b=names_ext[names_ext['area'].str.contains('Brain')]
names_ext_b_20x=names_ext_b[names_ext_b['objective'].str.contains('20x')]

#get FULL 63x images
names_ext_b_63x=names_ext_b[names_ext_b['objective'].str.contains('63x')].drop_duplicates()
names_ext_b_63x_full=names_ext_b_63x.groupby(names_ext_b_63x['slide_code']).aggregate({'tile' : ', '.join})
if not names_ext_b_63x.empty:
    names_ext_b_63x_full=names_ext_b_63x_full[names_ext_b_63x_full['tile'].str.contains(r'(?=.*left_dorsal)(?=.*right_dorsal)(?=.*ventral)(?=.*null)',regex=True)]
    names_ext_b_63x_full['tile'] = names_ext_b_63x_full['tile'].str.replace(r'\, null', '')
    names_ext_b_63x_full['slide_code']=names_ext_b_63x_full.index
    names_ext_b_63x_full.index.name = None
    names_ext_b_63x=names_ext_b_63x.drop(['tile'], axis=1)
    names_ext_b_63x=names_ext_b_63x.drop_duplicates()
    names_ext_b_63x_full=names_ext_b_63x_full.merge(names_ext_b_63x, how='left', on='slide_code')

#split out VNC TODO report if any VNC images are not 20x, for now just takes 63x over 20x if 63x exists so should be visible in tsvs
names_ext_v=names_ext[names_ext['area'].str.contains('VNC')]
#names_ext_v=names_ext_v.sort_values(by='objective')
#names_ext_v=names_ext_v.drop_duplicates('label', keep='last')
names_ext_v=names_ext_v[names_ext_v['objective'].str.contains('20x')]

#concat back
names_ext=pd.concat([names_ext_b_20x, names_ext_b_63x_full, names_ext_v]).reset_index()

##add part_of column
#add blank columns
names_ext['part_of']='' #fillna('')
names_ext['Template']=''

#fill template column with terms based on 'area' column of janelia .json
for i in range(len(names_ext)):
    if names_ext['area'][i] == 'Brain':
        names_ext['Template'][i]= 'JRC2018Unisex_c'
    elif names_ext['area'][i] == 'VNC':
        names_ext['Template'][i]= 'JRC2018UnisexVNC_c'
    else:
        print('an image is not of the VNS or brain')
#fill part_of column with terms based on 'gender' column of janelia .json
for i in range(len(names_ext)):
    if names_ext['gender'][i] == 'Female':
        names_ext['part_of'][i]='female organism|'
    elif names_ext['gender'][i] == 'Male':
        names_ext['part_of'][i]='male organism|'
    else:
        print('an image is not of a male or female')
#fill part_of column with terms based on 'area' column of janelia .json
for i in range(len(names_ext)):
    if names_ext['area'][i] == 'Brain':
        names_ext['part_of'][i]= names_ext['part_of'][i] + 'adult brain'
    elif names_ext['area'][i] == 'VNC':
        names_ext['part_of'][i]= names_ext['part_of'][i] + 'adult ventral nerve cord'
    else:
        print('an image is not of the VNS or brain')

#fill comments column #TODO add tile, sex, age, line and add column to final tsvs for loading
names_ext['comment']='tile(s): \'' + names_ext['tile'] + '\', effector genotype: \'' + names_ext['JRC Genotype'] + '\', objective: \'' + names_ext['objectiveName'] + '\', mounting protocol: \'' + names_ext['mounting_protocol'] + '\', slide_code: \'' + names_ext['slide_code'] + '\', age: \'' + names_ext['age'] + '\''

##add AD and DBD construct columns from Gillian's split table2
#load split table and extract relevant columns
janelia_codes = pd.read_csv(splits, sep='\t', index_col=False)
janelia_ext = janelia_codes[['#FL combination symbol', 'AD:construct', 'DBD:construct']]
#merge splits table and janelia data table
cur_tsv = pd.DataFrame.merge(names_ext, janelia_ext, how="left", left_on='publishing_name', right_on='#FL combination symbol')
#extract columns required for curation tsv file
cur_tsv = cur_tsv[['filename', 'label', 'AD:construct', 'DBD:construct', 'part_of', 'Template', 'line', 'comment']]
#rename AD, DBD using their names, and line to synonyms
cur_tsv = cur_tsv.rename(columns={'AD:construct':'AD', 'DBD:construct':'DBD', 'line':'synonyms'})
#replace nan with ''
cur_tsv = cur_tsv.fillna('')

#add JRC_ and no prefix synonyms TODO just remove the first 4 characters or report if nothing is removed (still possible that there are other prefixes)
#TODO simplify this!
cur_tsv['synonyms']=cur_tsv['synonyms'].str.replace('GMR_', '').str.replace('JRC_', '').str.replace('BJD_', '').str.replace('JHS_', '') + ' ' + cur_tsv['synonyms'] + ' ' + 'JRC_' + cur_tsv['synonyms'].str.replace('GMR_', '').str.replace('JRC_', '').str.replace('BJD_', '')
cur_tsv['synonyms'] = cur_tsv['synonyms'].apply(lambda x: ' '.join(pd.unique(x.split())))
cur_tsv['synonyms'] = cur_tsv['synonyms'].str.replace(' ', '|')


##Identify rows with missing hemidrivers and save as a separate file
#Identify rows with missing hemidrivers
cur_missing_tsv=cur_tsv[(cur_tsv.AD == 'NOT_IN_FB') | (cur_tsv.AD == '') | (cur_tsv.DBD == 'NOT_IN_FB') | (cur_tsv.DBD == '')]
#write missing hemis tsv for fixing when available
if not cur_missing_tsv.empty:
    cur_missing_tsv.to_csv('/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/problem_records/split_missing_hemis_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)
#remove missing rows with missing hemisdrivers from cur_tsv
cur_tsv=cur_tsv[~(cur_tsv.AD == 'NOT_IN_FB') & ~(cur_tsv.AD == '') & ~(cur_tsv.DBD == 'NOT_IN_FB') & ~(cur_tsv.DBD == '')]

#write .tsv file for curation. Using names ext for now as lacking hemidrivers
cur_tsv.to_csv('/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/curation_tsvs/split_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)
names_ext.to_csv('/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/archive/allsplit_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)