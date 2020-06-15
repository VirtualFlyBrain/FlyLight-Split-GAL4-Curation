#import libraries
import json
import pandas as pd

#manually set DOI/ds (should be args)
DOI = '10.1101/404277'
#(date should not be manual)
ds = 'newmeta_Dolan2019_200601'

#load Janelia splits .json as dict.
data = json.load(open('Janelia_API.json'))

#convert janelia splits .json images data to dataframe.
df = pd.DataFrame(data["images"])

#select only rows with chosen doi.
df_paper = df[df['doi'].str.contains(DOI, na=False)]

#extract only pub_name and roi columns
df_paper_ext = df_paper[["publishing_name", "roi"]]

#take only unique pub_names
df_pub_uni = df_paper_ext['publishing_name'].unique()




#
map_rois = pd.read_table('Dolan2019_unique_rois_FBbt_Map.tsv', engine='python'.replace('"',''), index_col=0)

result = pd.DataFrame.merge(map_rois, df_paper_ext, how="right", left_on='roi', right_on='roi')

result_uni = result.drop_duplicates()

del result_uni['roi']

result_uni.to_csv(ds + '.tsv', sep = '\t', index = False)