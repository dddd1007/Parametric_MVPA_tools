def batch_paramatric_GLM(nii_root_dir, sub_num_list, total_session_num, all_sub_dataframe, params_name, contrast_list, cache_folder, result_folder, parallel_cores):

    from nipype import Node, Workflow, Function
    from nipype.interfaces.spm import Level1Design, EstimateModel, EstimateContrast
    from nipype.algorithms.modelgen import SpecifySPMModel
    from nipype.interfaces.utility import IdentityInterface
    from nipype import DataSink

    # Define the helper functions

    def nii_selector(root_dir, sub_num, session_num, all_sub_dataframe, data_type="Smooth_8mm"):
        import os
        import glob
        session_list = ["session" + str(i)
                        for i in range(1, session_num+1)]
        sub_name = "sub"+str(sub_num)
        # print(file_path)
        nii_list = []
        for s in session_list:
            file_path = os.path.join(root_dir, sub_name, data_type, s)
            nii_list.append(glob.glob(file_path + "/*.nii"))
        single_sub_data = all_sub_dataframe[all_sub_dataframe.Subject_num == sub_num]
        return (nii_list, single_sub_data, sub_name)

    def condition_generator(single_sub_data, params_name, duration=2):
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
                                pmod=[Bunch(name=pmod_names, poly=pmod_poly, param=pmod_params)])
            subject_info.append(tmp_Bunch)

        return subject_info

    # Define each Nodes in the workflow

    NiiSelector = Node(Function(input_names=["root_dir", "sub_num", "session_num", "all_sub_dataframe", "data_type"],
                                output_names=[
                                    "nii_list", "single_sub_data", "sub_name"],
                                function=nii_selector), name="NiiSelector")

    ConditionGenerator = Node(Function(input_names=["single_sub_data", "params_name", "duration"],
                                        output_names=["subject_info"],
                                        function=condition_generator), name="ConditionGenerator")

    glm_input = Node(IdentityInterface(fields=['nii_list', 'single_sub_data', 'params_name', 'contrast_list'],
                                        mandatory_inputs=True), name="glm_input")

    # SpecifyModel - Generates SPM-specific Model
    modelspec = Node(SpecifySPMModel(concatenate_runs=False,
                                        input_units='scans',
                                        output_units='scans',
                                        time_repetition=2,
                                        high_pass_filter_cutoff=128),
                        name="modelspec")

    # Level1Design - Generates an SPM design matrix
    level1design = Node(Level1Design(bases={'hrf': {'derivs': [0, 0]}},
                                        timing_units='scans',
                                        interscan_interval=2),
                        name="level1design")

    level1estimate = Node(EstimateModel(
        estimation_method={'Classical': 1}), name="level1estimate")

    level1conest = Node(EstimateContrast(), name="level1conest")

    OutputNode = Node(DataSink(), name="OutputNode")

    # Define the attributes of those nodes

    NiiSelector.inputs.root_dir = nii_root_dir
    NiiSelector.iterables = ("sub_num", sub_num_list)
    NiiSelector.inputs.session_num = total_session_num
    NiiSelector.inputs.data_type = "Smooth_8mm" 
    NiiSelector.inputs.all_sub_dataframe = all_sub_dataframe

    glm_input.inputs.params_name = params_name
    glm_input.inputs.contrast_list = contrast_list

    OutputNode.inputs.base_directory = result_folder

    # Define the workflows

    single_sub_GLM_wf = Workflow(name='single_sub_GLM_wf')
    single_sub_GLM_wf.connect([(glm_input, ConditionGenerator, [('single_sub_data', 'single_sub_data'),
                                                                ('params_name', 'params_name')]),
                                (glm_input, modelspec, [
                                ('nii_list', 'functional_runs')]),
                                (glm_input, level1conest, [
                                ('contrast_list', 'contrasts')]),
                                (ConditionGenerator, modelspec, [
                                    ('subject_info', 'subject_info')]),
                                (modelspec, level1design, [
                                ('session_info', 'session_info')]),
                                (level1design, level1estimate, [
                                ('spm_mat_file', 'spm_mat_file')]),
                                (level1estimate, level1conest, [('spm_mat_file', 'spm_mat_file'),
                                                                ('beta_images',
                                                                'beta_images'),
                                                                ('residual_image', 'residual_image')])])

    batch_GLM_wf = Workflow(name="batch_GLM_wf",
                            base_dir=cache_folder)
    batch_GLM_wf.connect([(NiiSelector, single_sub_GLM_wf, [('nii_list', 'glm_input.nii_list'),
                                                            ('single_sub_data', 'glm_input.single_sub_data')]),
                            (NiiSelector, OutputNode, [('sub_name', 'container')]),
                            (single_sub_GLM_wf, OutputNode, [('level1conest.spm_mat_file', '1stLevel.@spm_mat'),
                                                            ('level1conest.spmT_images',
                                                            '1stLevel.@T'),
                                                            ('level1conest.con_images',
                                                            '1stLevel.@con'),
                                                            ('level1conest.spmF_images',
                                                            '1stLevel.@F'),
                                                            ('level1conest.ess_images', '1stLevel.@ess')])])

    # Excute the workflow
    batch_GLM_wf.run(plugin='MultiProc', plugin_args={'n_procs' : parallel_cores})
