# Single subject parameters analysis by GLM in fMRI
# Author: Xiaokai Xia (xia@xiaokai.me)
# Date: 2020-12-9

# This script try to analysis build a design matric for parametric analysis and excute a GLM
# to discover the relationhip between subject parameters and BOLD signal.

import numpy as np
import pandas as pd
from nipype.interfaces.spm import Level1Design, EstimateModel, EstimateContrast
from nipype.algorithms.modelgen import SpecifySPMModel
from nipype.interfaces.utility import Function, IdentityInterface
from nipype.interfaces.io import SelectFiles, DataSink
from nipype import Workflow, Node
from nipype.interfaces.base import Bunch

# Retrive the nii files which will be used
def nii_selector(root_dir, sub, session_num, data_type = "Smooth_8mm"):
    """Retrive the path of nii files
    
    Retrive the nii files path from Lingwang's pre-process directory structure.

    Args:
        root_dir: Root directory location, which contains all subjects data. 
                  You will see like "sub1" and so on in this directory.
        sub:      The subject you want to analysis.
        session_num: Total number of sessions. e.g 'session_num = 6' mean you have six sessions
        data_type: You can specify "Smooth_8mm" or "Normalized" to select specific type of data.
    
    Returns: 
        nii_list: All nii files for this subject.
    """
    import os
    import glob
    session_list = ["session" + str(i) for i in range(1, session_num+1)]
    
    # print(file_path)
    nii_list = []
    for s in session_list:
        file_path = os.path.join(root_dir, sub, data_type, s)
        nii_list.append(glob.glob(file_path + "/*.nii"))

    return nii_list

# Build the relationship between onsets and parameters
def condition_generator(single_sub_data, params_name, duration = 2):
    """Build a bunch to show the relationship between each onset and parameter

    Build a bunch for make a design matrix for next analysis. This bunch is for describing the relationship
    between each onset and parameter.

    Args:
        single_sub_data: A pandas DataFrame which contains data for one subject. 
                         It must contains the information about run, onsets, and parameters.
        params_name: A list of names of parameters which you want to analysis. 
                     The order of the names will be inherited to the design matrix next.
        duration: The duration of a TR.

    Returns:
        subject_info: A list of bunch type which can be resolve by SpecifySPMModel interface in nipype.
    """
    from nipype.interfaces.base import Bunch
    run_num = set(single_sub_data.run)
    subject_info = []
    for i in run_num:
        tmp_table = single_sub_data[single_sub_data.run == i]
        tmp_onset = tmp_table.onset.values.tolist()

        pmod_names = []
        pmod_params = []
        pmod_poly = []
        for param in params_name:
            pmod_params.append(tmp_table[param].values.tolist())
            pmod_names.append(param)
            pmod_poly.append(1)

        tmp_Bunch = Bunch(conditions=["trial_onset_run"+str(i)], onsets=[tmp_onset], durations=[[duration]], 
                          pmod=[Bunch(name = pmod_names, poly = pmod_poly, param = pmod_params)])
        subject_info.append(tmp_Bunch)
    return subject_info