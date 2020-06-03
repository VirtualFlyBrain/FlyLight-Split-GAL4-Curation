# FlyLight Split-GAL4 Curation
A repository for code to create curation records for Janelia FlyLight Split-GAL4 images.

**Contents**
Python script for creating curation record tsv files for a given doi and ds name and datafiles from Janelia FlyLight API along with Gillian's FlyLight combination lines tsv file.

**Git Workflow**
Current:
Run JRC2018_ds_tsv_for_curation.py, specifying doi and ds name (currently need to edit the script to do so). Script will pull required fields from JRC2018_Unisex_20X_split_fileNames1.csv and JRC2018_VNC_Unisex_split_fileNames1.csv to get image filenames and publishing names of split-GAL4 lines, then extract hemidriver names from flylight_combination_lines_2.tsv. YAML files must currently be created manually.

Planned:
Working on implementing a re-useable pipeline to reduce the requirement for co-ordination, workflow to be updated.

Curation files created with this code are loaded through the [curation repo](https://github.com/VirtualFlyBrain/curation).


