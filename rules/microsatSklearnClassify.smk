__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2020 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'


def microsatSklearnClassify(
        in_evaluated="microsat/{sample}_microsatLenDistrib.json",
        in_model="microsat/microsatModel.json",
        out_report="microsat/{sample}_stabilityStatus.json",
        out_stderr="logs/{sample}_microsatStabilityClassify_stderr.txt",
        params_classifier=None,
        params_classifier_params=None,
        params_consensus_method="ratio",
        params_data_key=None,
        params_instability_ratio=None,
        params_instability_count=None,
        params_locus_weight_is_score=False,
        params_min_depth=None,
        params_min_voting_loci=None,
        params_random_seed=None,
        params_status_key=None,
        params_undetermined_weight=None,
        params_keep_output=False,
        params_stderr_append=False):
    """Predict stability classes and scores for loci and samples using an sklearn classifer."""
    rule microsatSklearnClassify:
        input:
            evaluated = in_evaluated,
            model = in_model
        output:
            out_report if params_keep_output else temp(out_report)
        log:
            out_stderr
        params:
            bin_path = os.path.abspath(os.path.join(workflow.basedir, "scripts/microsatSklearnClassify.py")),
            classifier = "" if params_classifier is None else "--classifier {}".format(params_classifier),
            classifier_params = "" if params_classifier_params is None else "--classifier-params {}".format(params_classifier_params),
            consensus_method = "" if params_consensus_method is None else "--consensus-method {}".format(params_consensus_method),
            data_key = "" if params_data_key is None else "--data-key {}".format(params_data_key),
            instability_ratio = "" if params_instability_ratio is None or params_consensus_method == "count" else "--instability-ratio {}".format(params_instability_ratio),
            instability_count = "" if params_instability_count is None or params_consensus_method == "ratio" else "--instability-ratio {}".format(params_instability_count),
            locus_weight_is_score = "" if params_locus_weight_is_score is None else "--locus-weight-is-score",
            min_depth = "" if params_min_depth is None else "--min-support {}".format(params_min_depth),
            min_voting_loci = "" if params_min_voting_loci is None else "--min-voting-loci {}".format(params_min_voting_loci),
            random_seed = "" if params_random_seed is None else "--random-seed {}".format(params_random_seed),
            status_key = "" if params_status_key is None else "--status-key {}".format(params_status_key),
            stderr_redirection = "2>" if not params_stderr_append else "2>>",
            undetermined_weight = "" if params_undetermined_weight is None else "--undetermined-weight {}".format(params_undetermined_weight),
        conda:
            "envs/anacore-sklearn.yml"
        shell:
            "{params.bin_path}"
            " {params.classifier}"
            " {params.classifier_params}"
            " {params.consensus_method}"
            " {params.data_key}"
            " {params.instability_ratio}"
            " {params.instability_count}"
            " {params.locus_weight_is_score}"
            " {params.min_depth}"
            " {params.random_seed}"
            " {params.status_key}"
            " {params.undetermined_weight}"
            " --input-evaluated {input.evaluated}"
            " --input-model {input.model}"
            " --output-report {output}"
            " {params.stderr_redirection} {log}"
