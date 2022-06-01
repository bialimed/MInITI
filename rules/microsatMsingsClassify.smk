__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2020 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'

    group_locus.add_argument('-p', '--peak-height-cutoff', default=0.05, type=float, help='Minimum height to consider a peak in size distribution as rate of the highest peak. [Default: %(default)s]')
    group_locus.add_argument('-s', '--std-dev-rate', default=2.0, type=float, help='The locus is tagged as unstable if the number of peaks is upper than models_avg_nb_peaks + std_dev_rate * models_std_dev_nb_peaks. [Default: %(default)s]')
    
def microsatMSINGSClassify(
        in_evaluated="microsat/{sample}_microsatLenDistrib.json",
        in_model="microsat/microsatModel.json",
        out_report="microsat/{sample}_stabilityStatus.json",
        out_stderr="logs/{sample}_microsatMSINGSClassify_stderr.txt",
        params_consensus_method="ratio",
        params_data_key=None,
        params_instability_ratio=None,
        params_instability_count=None,
        params_locus_weight_is_score=False,
        params_min_depth=None,
        params_min_voting_loci=None,
        params_peak_height_cutoff=None,
        params_status_key=None,
        params_std_dev_rate=None,
        params_undetermined_weight=None,
        params_keep_output=False,
        params_stderr_append=False):
    """Predict stability classes and scores for loci and samples using mSINGS v4.0 like algorithm."""
    rule microsatMSINGSClassify:
        input:
            evaluated = in_evaluated,
            model = in_model
        output:
            out_report if params_keep_output else temp(out_report)
        log:
            out_stderr
        params:
            bin_path = "microsatMsingsClassify.py",
            consensus_method = "" if params_consensus_method is None else "--consensus-method {}".format(params_consensus_method),
            data_key = "" if params_data_key is None else "--data-key {}".format(params_data_key),
            instability_ratio = "" if params_instability_ratio is None or params_consensus_method == "count" else "--instability-ratio {}".format(params_instability_ratio),
            instability_count = "" if params_instability_count is None or params_consensus_method == "ratio" else "--instability-ratio {}".format(params_instability_count),
            locus_weight_is_score = "" if params_locus_weight_is_score is None else "--locus-weight-is-score",
            method_name = "" if params_method_name is None else "--method-name {}".format(params_method_name),
            min_depth = "" if params_min_depth is None else "--min-support {}".format(params_min_depth),
            min_voting_loci = "" if params_min_voting_loci is None else "--min-voting-loci {}".format(params_min_voting_loci),
            peak_height_cutoff = "" if params_peak_height_cutoff is None else "--peak-height-cutoff {}".format(params_peak_height_cutoff),
            random_seed = "" if params_random_seed is None else "--random-seed {}".format(params_random_seed),
            status_key = "" if params_status_key is None else "--status-key {}".format(params_status_key),
            std_dev_rate = "" if params_std_dev_rate is None else "--std-dev-rate {}".format(params_std_dev_rate),
            stderr_redirection = "2>" if not params_stderr_append else "2>>",
            undetermined_weight = "" if params_undetermined_weight is None else "--undetermined-weight {}".format(params_undetermined_weight),
        conda:
            "envs/anacore-utils.yml"
        shell:
            "{params.bin_path}"
            " {params.consensus_method}"
            " {params.data_key}"
            " {params.instability_ratio}"
            " {params.instability_count}"
            " {params.locus_weight_is_score}"
            " {params.method_name}"
            " {params.min_depth}"
            " {params.peak_height_cutoff}"
            " {params.random_seed}"
            " {params.status_key}"
            " {params.std_dev_rate}"
            " {params.undetermined_weight}"
            " --input-evaluated {input.evaluated}"
            " --input-model {input.model}"
            " --output-report {output}"
            " {params.stderr_redirection} {log}"
