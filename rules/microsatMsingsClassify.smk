__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2020 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'


def microsatMsingsClassify(
        in_evaluated="microsat/{sample}_microsatLenDistrib.json",
        in_model="microsat/microsatModel.json",
        out_report="microsat/{sample}_stabilityStatus.json",
        out_stderr="logs/{sample}_microsatMSINGSClassify_stderr.txt",
        params_consensus_method="ratio",
        params_data_method=None,
        params_instability_ratio=None,
        params_instability_count=None,
        params_locus_weight_is_score=False,
        params_min_depth=None,
        params_min_voting_loci=None,
        params_peak_height_cutoff=None,
        params_status_method=None,
        params_std_dev_rate=None,
        params_undetermined_weight=None,
        params_keep_output=False,
        params_stderr_append=False):
    """Predict stability classes and scores for loci and samples using mSINGS v4.0 like algorithm."""
    rule microsatMsingsClassify:
        input:
            evaluated = in_evaluated,
            model = in_model
        output:
            out_report if params_keep_output else temp(out_report)
        log:
            out_stderr
        params:
            bin_path = os.path.abspath(os.path.join(workflow.basedir, "scripts/microsatMsingsClassify.py")),
            consensus_method = "" if params_consensus_method is None else "--consensus-method {}".format(params_consensus_method),
            data_method = "" if params_data_method is None else "--data-method {}".format(params_data_method),
            instability_ratio = "" if params_instability_ratio is None or params_consensus_method == "count" else "--instability-ratio {}".format(params_instability_ratio),
            instability_count = "" if params_instability_count is None or params_consensus_method == "ratio" else "--instability-ratio {}".format(params_instability_count),
            locus_weight_is_score = "" if params_locus_weight_is_score is None else "--locus-weight-is-score",
            min_depth = "" if params_min_depth is None else "--min-depth {}".format(params_min_depth),
            min_voting_loci = "" if params_min_voting_loci is None else "--min-voting-loci {}".format(params_min_voting_loci),
            peak_height_cutoff = "" if params_peak_height_cutoff is None else "--peak-height-cutoff {}".format(params_peak_height_cutoff),
            status_method = "" if params_status_method is None else "--status-method {}".format(params_status_method),
            std_dev_rate = "" if params_std_dev_rate is None else "--std-dev-rate {}".format(params_std_dev_rate),
            stderr_redirection = "2>" if not params_stderr_append else "2>>",
            undetermined_weight = "" if params_undetermined_weight is None else "--undetermined-weight {}".format(params_undetermined_weight),
        conda:
            "envs/anacore-sklearn.yml"
        shell:
            "{params.bin_path}"
            " {params.consensus_method}"
            " {params.data_method}"
            " {params.instability_ratio}"
            " {params.instability_count}"
            " {params.locus_weight_is_score}"
            " {params.min_depth}"
            " {params.peak_height_cutoff}"
            " {params.status_method}"
            " {params.std_dev_rate}"
            " {params.undetermined_weight}"
            " --input-evaluated {input.evaluated}"
            " --input-model {input.model}"
            " --output-report {output}"
            " {params.stderr_redirection} {log}"
