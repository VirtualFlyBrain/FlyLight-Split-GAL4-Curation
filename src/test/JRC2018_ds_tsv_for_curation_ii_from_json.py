#import libraries
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import argparse
import yaml
import json
from datetime import date

#Setup arguments for argparse to allow input of ds, doi and filepaths in terminal
#parser = argparse.ArgumentParser(description='Accepts paper DOI and ds name and pathnames to datafiles (see args). Returns a tsv file with "filename", "label", "AD:construct", "DBD:construct" and "part_of" for entry into the VFB curation interface.')
#parser.add_argument('--doi', '-doi', type=str, help='A string referring to the DOI, use "|" to merge results from multiple DOIs')
#parser.add_argument('--year', '-y', type=str, help='A string to be appended to the filename to indicate data batch')
#parser.add_argument('--ds', '-ds', type=str, help='A string to name the dataset (omit split_)')
#parser.add_argument('--janelia_json', '-f', type=str, help='path to most recent janelia json')
#parser.add_argument('--splits', '-s', type=str, help='path to flylight_combination_lines_2.tsv')
#parser.add_argument('--curator', '-c', type=str, help='curator name, must be in KB')
#args = vars(parser.parse_args())

##args for testing in ide (should be commented out)
doi = '10.7554/elife.34272'
ds = 'Namiki2018'
year = '2018'
janelia_json_new = '/Users/alexmclachlan/Downloads/janelia_2020_12_15.json'
splits = '/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/resources/flylight_combination_lines_2.tsv'
stochastic_effectors = '/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/resources/stochastic_effectors_list_01_2021.tsv'
curator = 'adm71'

#asign args to variables
#doi = args['doi']
#ds = args['ds']
#year = args['year']
#janelia_json = args['filenames']
#splits = args['splits']
#curator = args['curator']

##create yaml data and write file
#yaml data
yaml_data = dict(
    DataSet=ds,
    Imaging_type='confocal microscopy',
    Curator=curator)
#write yaml file
with open('split_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.yaml', 'w') as outfile:
    yaml.dump(yaml_data, outfile, default_flow_style=False)

##get all relevant data from janelia .json
#extract only rows with appropriate doi
with open(janelia_json_new) as f:
   current_data = json.load(f)

janelia_df=pd.DataFrame(current_data['images'])

#extract only rows with appropriate doi
janelia_df = janelia_df[janelia_df['doi'].str.contains(doi, na=False)].reset_index()

#extract relevant columns
names_ext = janelia_df[['publishing_name', 'ad', 'dbd', 'gender', 'area', 'slide_code', 'objective', 'sampleId', 'tile', 'age', 'published_externally', 'effector']]

#remove rows where 'published_externally' does not = 1
names_ext = names_ext[names_ext['publishing_name'].str.contains('1', na=False)].reset_index()

##remove stochastic effectors.
#load stochastic_effectors tsv file to df
stochastic_effectors=pd.read_csv(stochastic_effectors, sep='\t', index_col=False)
#drop rows with effectors matching any of the stochastic_effectors
names_ext[~names_ext['effector'].str.contains(list(stochastic_effectors['Effector']))] #TODO fix this to work with a list somehow


##add label
#add info from fields to label
names_ext['label']= 'JRC_' + names_ext['publishing_name'] + '_' + names_ext['area'] + '_' + year +'_' + names_ext['slide_code']
#fill filename column with 'objective-area-sampleid'
names_ext['filename']=names_ext['objective'] + '-' + names_ext['area'] + '-' +  names_ext['sampleId']


##extract unique brains, taking 63x over 20x where possible
#split out brain
names_ext_b=names_ext[names_ext['area'].str.contains('Brain')]
names_ext_b=names_ext_b.sort_values(by='objective')
names_ext_b=names_ext_b.drop_duplicates('label', keep='last')

#split out VNC
names_ext_v=names_ext[names_ext['area'].str.contains('VNC')]
names_ext_v=names_ext_v.sort_values(by='objective')
names_ext_v=names_ext_v.drop_duplicates('label', keep='last')

#concat back
names_ext=pd.concat([names_ext_b, names_ext_v]).reset_index()

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
        names_ext['part_of'][i]= names_ext['part_of'][i] + 'adult ventral nervous system'
    else:
        print('an image is not of the VNS or brain')

##add AD and DBD construct columns from Gillian's split table2
#load split table and extract relevant columns
janelia_codes = pd.read_csv(splits, sep='\t', index_col=False)
janelia_ext = janelia_codes[['#FL combination symbol', 'AD:construct', 'DBD:construct']]
#merge splits table and janelia data table
cur_tsv = pd.DataFrame.merge(names_ext, janelia_ext, how="left", left_on='publishing_name', right_on='#FL combination symbol')
#extract columns required for curation tsv file
cur_tsv = cur_tsv[['filename', 'label', 'AD:construct', 'DBD:construct', 'part_of', 'Template']]
#rename AD, DBD using their names
cur_tsv = cur_tsv.rename(columns={'AD:construct':'AD', 'DBD:construct':'DBD'})
#replace nan with ''
cur_tsv = cur_tsv.fillna('')

##Identify rows with missing hemidrivers and save as a separate file
#Identify rows with missing hemidrivers
cur_missing_tsv=cur_tsv[(cur_tsv.AD == 'NOT_IN_FB') | (cur_tsv.AD == '') | (cur_tsv.DBD == 'NOT_IN_FB') | (cur_tsv.DBD == '')]
#write missing hemis tsv for fixing when available
if not cur_missing_tsv.empty:
    cur_missing_tsv.to_csv('split_missing_hemis_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)
#remove missing rows with missing hemisdrivers from cur_tsv
cur_tsv=cur_tsv[~(cur_tsv.AD == 'NOT_IN_FB') & ~(cur_tsv.AD == '') & ~(cur_tsv.DBD == 'NOT_IN_FB') & ~(cur_tsv.DBD == '')]

#write .tsv file for curation. Using names ext for now as lacking hemidrivers
cur_tsv.to_csv('split_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)
names_ext.to_csv('allsplit_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)