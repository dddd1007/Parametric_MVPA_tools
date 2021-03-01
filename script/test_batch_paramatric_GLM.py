from batch_paramatric_GLM import batch_paramatric_GLM

import pandas as pd
all_data = pd.read_csv("/media/psf/Home/project2git/fmri_analysis2_nipype_type/data/behavioral_data/all_data_with_2a1d1CCC.csv")

# condition names
condition_names = ["trial_onset_run1", "trial_onset_run1x_2a1d1CCC^1",
                   "trial_onset_run2", "trial_onset_run2x_2a1d1CCC^1",
                   "trial_onset_run3", "trial_onset_run3x_2a1d1CCC^1",
                   "trial_onset_run4", "trial_onset_run4x_2a1d1CCC^1",
                   "trial_onset_run5", "trial_onset_run5x_2a1d1CCC^1",
                   "trial_onset_run6", "trial_onset_run6x_2a1d1CCC^1"]
cont1 = ["p_value", 'T', condition_names, [0,1,0,1,0,1,0,1,0,1,0,1]]
contrast_list = [cont1]

batch_paramatric_GLM(nii_root_dir = "/media/psf/Home/project2git/fmri_analysis2_nipype_type/data/preprocessed/Wang", 
                    sub_num_list = [1,2,3,4,5,6,7,8,9,10],
                    total_session_num = 6,
                    all_sub_dataframe = all_data,
                    params_name = ["_2a1d1CCC"],
                    contrast_list = contrast_list,
                    cache_folder = "/media/psf/Home/project2git/fmri_analysis2_nipype_type/data/output/tmp",
                    result_folder = "/media/psf/Home/project2git/fmri_analysis2_nipype_type/data/output/level1_3",
                    parallel_cores = 1)
