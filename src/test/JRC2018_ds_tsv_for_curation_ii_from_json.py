#import libraries
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import argparse
import yaml
import json
import gzip
from datetime import date

#Setup arguments for argparse to allow input of ds, doi and filepaths in terminal
#parser = argparse.ArgumentParser(description='Accepts paper DOI and ds name and pathnames to datafiles (see args). Returns a tsv file with "filename", "label", "AD:construct", "DBD:construct" and "part_of" for entry into the VFB curation interface.')
#parser.add_argument('--doi', '-doi', type=str, help='A string referring to the DOI, use "|" to merge results from multiple DOIs')
#parser.add_argument('--year', '-y', type=str, help='A string to be appended to the filename to indicate data batch')
#parser.add_argument('--ds', '-ds', type=str, help='A string to name the dataset (omit split_)')
#parser.add_argument('--filenames', '-f', type=str, help='path to filenames csv (brain or vnc)')
#parser.add_argument('--splits', '-s', type=str, help='path to flylight_combination_lines_2.tsv')
#parser.add_argument('--curator', '-c', type=str, help='curator name, must be in KB')
#args = vars(parser.parse_args())

##args for testing in ide (should be commented out)
doi = '10.1016/j.cub.2020.07.083'
ds = 'Wang2020'
year = '2020'
#filenames = 
splits = '/Users/adm71/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/resources/flylight_combination_lines_2.tsv'
curator = 'adm71'

#asign args to variables
#doi = args['doi']
#ds = args['ds']
#year = args['year']
#filenames = args['filenames']
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
#read brain and TAG csv files made from janelia .json file
#filenames = pd.read_csv(filenames)
#tidy data by removing leading and trailing whitespaces
#filenames.columns = filenames.columns.str.strip()
#extract only rows with appropriate doi
#filenames = filenames[filenames['doi'].str.contains(doi, na=False)].reset_index()
with gzip.open('/Users/adm71/Documents/GitHub/Management/Janelia/JaneliaWorkstationAPI/vfb_images_2020_09_11.json.gz') as f:
   current_data = json.load(f)

janelia_df=pd.DataFrame(current_data['images'])
#extract only rows with appropriate doi
janelia_df = janelia_df[janelia_df['doi'].str.contains(doi, na=False)].reset_index()

#extract relevant columns
names_ext = janelia_df[['publishing_name', 'ad', 'dbd', 'gender', 'area', 'slide_code']]
#add missing filename column
names_ext['filename']=''
##add label
#add info from fields
names_ext['label']= 'JRC_' + names_ext['publishing_name'] + '_' + names_ext['area'] + '_' + year +'_' + names_ext['slide_code']
#remove slide code field
names_ext = names_ext.drop(['slide_code'], axis=1)

##add part_of column
#add blank part_of column
names_ext['part_of']='' #fillna('')
names_ext['template']=''
#fill template column with terms based on 'area' column of janelia .json
for i in range(len(names_ext)):
    if names_ext['area'][i] == 'Brain':
        names_ext['template'][i]= 'JRC2018Unisex_c'
    elif names_ext['area'][i] == 'VNC':
        names_ext['template'][i]= 'JRC2018UnisexVNC_c'
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
        names_ext['part_of'][i]= names_ext['part_of'][i] + 'thoracico-abdominal ganglion'
    else:
        print('an image is not of the VNS or brain')

##add AD and DBD construct columns from Gillian's split table2
#load split table and extract relevant columns
janelia_codes = pd.read_csv(splits, sep='\t', index_col=False)
janelia_ext = janelia_codes[['#FL combination symbol', 'AD:construct', 'DBD:construct']]
#merge splits table and janelia data table
cur_tsv = pd.DataFrame.merge(names_ext, janelia_ext, how="left", left_on='publishing_name', right_on='#FL combination symbol')
#extract columns required for curation tsv file
cur_tsv = cur_tsv[['filename', 'label', 'AD:construct', 'DBD:construct', 'part_of', 'template']]
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
#cur_tsv.to_csv('split_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)
names_ext.to_csv('split_' + ds + '_' + date.today().strftime('%Y%m%d')[2:8] + '.tsv', sep = '\t', index = False)
