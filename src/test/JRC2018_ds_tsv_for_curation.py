#import libraries
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import argparse
import yaml
from datetime import date

#Setup arguments for argparse to allow input of ds, doi and filepaths in terminal
parser = argparse.ArgumentParser(description='Accepts paper DOI and ds name and pathnames to datafiles (see args). Returns a tsv file with "filename", "label", "AD:construct", "DBD:construct" and "part_of" for entry into the VFB curation interface.')
parser.add_argument('-doi', type=str, help='A string referring to the DOI, use "|" to merge results from multiple DOIs')
parser.add_argument('-ds', type=str, help='A string to name the dataset (omit split_)')
parser.add_argument('-year', type=str, help='A string to be appended to the filename to indicate data batch')
parser.add_argument('-brain', type=str, help='path to JRC2018_Unisex_20X_split_fileNames1.csv')
parser.add_argument('-vnc', type=str, help='path to JRC2018_VNC_Unisex_split_fileNames1.csv')
parser.add_argument('-splits', type=str, help='path to flylight_combination_lines_2.tsv')
args = vars(parser.parse_args())

#asign args to variables
doi = args['doi']
ds = args['ds']
year = args['year']
brain = args['brain']
vnc = args['vnc']
splits = args['splits']

##create yaml data and write file
#yaml data
yaml_data = dict(
    DataSet=ds,
    Template='JRC2018Unisex_c',
    Imaging_type='confocal microscopy',
    Curator='https://orcid.org/0000-0002-5214-8125')
#write yaml file
with open('split_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.yaml', 'w') as outfile:
    yaml.dump(yaml_data, outfile, default_flow_style=False)

##get all relevant data from janelia .json
#read brain and TAG csv files made from janelia .json file
brain_csv = pd.read_csv(brain)
TAG_csv = pd.read_csv(vnc)
#append TAG rows to brain rows
names = brain_csv.append(TAG_csv)
#tidy data by rimoving whitespaces
names.columns = names.columns.str.strip()
#extract only rows with appropriate doi
names = names[names['doi'].str.contains(doi, na=False)].reset_index()
#extract relevant columns
names_ext = names[['filename', 'publishing_name', 'ad', 'dbd', 'gender', 'area']]
##add label
#add info from fields
names_ext['label']= 'JRC_' + names_ext['publishing_name'] + '_' + names_ext['area'] + '_' + year +'_'
#calculate duplicate numbers and add as column
names_ext['dup_number'] = names_ext.groupby(['label']).cumcount()+1
names_ext.dup_number = names_ext.dup_number.astype(str)
#append duplicate number to label
names_ext['label']= names_ext['label'] + '_' + names_ext['dup_number']

##add part_of column
#add blank part_of column
names_ext['part_of']='nan'
#fill part_of column with terms based on 'area' column of janelia .json
for i in range(len(names)):
    if names_ext['area'][i] == 'Brain':
        names_ext['part_of'][i]='female organism|adult brain'
    elif names_ext['area'][i] == 'VNC':
        names_ext['part_of'][i]='female organism|thoracico-abdominal ganglion'

##add AD and DBD construct columns from Gillian's split table2
#load split table and extract relevant columns
janelia_codes = pd.read_csv(splits, sep='\t', index_col=False)
janelia_ext = janelia_codes[['#FL combination symbol', 'AD:construct', 'DBD:construct']]
#merge splits table and janelia data table
cur_tsv = pd.DataFrame.merge(names_ext, janelia_ext, how="left", left_on='publishing_name', right_on='#FL combination symbol')
#extract columns required for curation tsv file
cur_tsv = cur_tsv[['filename', 'label', 'AD:construct', 'DBD:construct', 'part_of']]
#rename AD, DBD using their names
cur_tsv = cur_tsv.rename(columns={'AD:construct':'AD', 'DBD:construct':'DBD'})

#write .tsv file for curation.
cur_tsv.to_csv('split_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)
