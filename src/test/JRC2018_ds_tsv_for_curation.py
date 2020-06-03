#import libraries
import pandas as pd
import argparse

#Setup arguments for argparse
parser = argparse.ArgumentParser(description='Accepts paper DOI and ds name and Returns a tsv file with "filename", "label", "AD:construct", "DBD:construct" and "part_of" for entry into the VFB curation interface.')
parser.add_argument('-doi', help='A string referring to the DOI')
parser.add_argument('-ds', type=str, help='A string to name the dataset (omit split_)')
args = vars(parser.parse_args())
doi = args['doi']
ds = args['ds']

#manually set doi and ds
#doi = '10.7554/elife.34272'
#ds = 'Namiki2018_200529'

##get all relevant data from janelia .json
#read brain and TAG csv files made from janelia .json file
brain_csv = pd.read_csv('/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/test/resources/JRC2018_Unisex_20X_split_fileNames1.csv')
TAG_csv = pd.read_csv('/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/test/resources/JRC2018_VNC_Unisex_split_fileNames1.csv')
#append TAG rows to brain rows
names = brain_csv.append(TAG_csv)
#tidy data by rimoving whitespaces
names.columns = names.columns.str.strip()
#extract only rows with appropriate doi
names = names[names['doi'].str.contains(doi, na=False)].reset_index()
#extract relevant columns
names_ext = names[['filename', 'publishing_name', 'ad', 'dbd', 'gender', 'area']]

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
janelia_codes = pd.read_csv('/Users/alexmclachlan/Documents/GitHub/FlyLight-Split-GAL4-Curation/src/test/resources/flylight_combination_lines_2.tsv', sep='\t', index_col=False)
janelia_ext = janelia_codes[['#FL combination symbol', 'AD:construct', 'DBD:construct']]
#merge splits table and janelia data table
cur_tsv = pd.DataFrame.merge(names_ext, janelia_ext, how="left", left_on='publishing_name', right_on='#FL combination symbol')
#add label column
cur_tsv['label']=cur_tsv['filename']
#extract columns required for curation tsv file
cur_tsv = cur_tsv[['filename', 'label', 'AD:construct', 'DBD:construct', 'part_of']]
#rename AD, DBD using their names
cur_tsv = cur_tsv.rename(columns={'AD:construct':'AD', 'DBD:construct':'DBD'})

#write .tsv file for curation.
cur_tsv.to_csv('split_' + ds + '.tsv', sep = '\t', index = False)
