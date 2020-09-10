__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2020 IUCT-O'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'


def microsatStabilityClassify(
        in_evaluated="microsat/{sample}_microsatLenDistrib.json",
        in_model="microsat/microsatModel.json",
        out_report="microsat/{sample}_stabilityStatus.json",
        out_stderr="logs/{sample}_microsatStabilityClassify_stderr.txt",
        params_classifier=None,
        params_classifier_params=None,
        params_consensus_method="ratio",
        params_instability_ratio=None,
        params_instability_count=None,
        params_locus_weight_is_score=False,
        params_method_name=None,
        params_min_support=None,
        params_min_voting_loci=None,
        params_random_seed=None,
        params_undetermined_weight=None,
        params_keep_output=False,
        params_stderr_append=False):
    """Predict stability classes and score for all samples loci."""
    rule microsatStabilityClassify:
        input:
            evaluated = in_evaluated,
            model = in_model
        output:
            out_report if params_keep_output else temp(out_report)
        log:
            out_stderr
        params:
            bin_path = "microsatStabilityClassify.py",
            classifier = "" if params_classifier is None else "--classifier {}".format(params_classifier),
            classifier_params = "" if params_classifier_params is None else "--classifier-params {}".format(params_classifier_params),
            consensus_method = "" if params_consensus_method is None else "--consensus-method {}".format(params_consensus_method),
            instability_ratio = "" if params_instability_ratio is None or params_consensus_method == "count" else "--instability-ratio {}".format(params_instability_ratio),
            instability_count = "" if params_instability_count is None or params_consensus_method == "ratio" else "--instability-ratio {}".format(params_instability_count),
            locus_weight_is_score = "" if params_locus_weight_is_score is None else "--locus-weight-is-score",
            method_name = "" if params_method_name is None else "--method-name {}".format(params_method_name),
            min_support = "" if params_min_support is None else "--min-support {}".format(params_min_support),
            min_voting_loci = "" if params_min_voting_loci is None else "--min-voting-loci {}".format(params_min_voting_loci),
            random_seed = "" if params_random_seed is None else "--random-seed {}".format(params_random_seed),
            stderr_redirection = "2>" if not params_stderr_append else "2>>",
            undetermined_weight = "" if params_undetermined_weight is None else "--undetermined-weight {}".format(params_undetermined_weight),
        conda:
            "envs/anacore-sklearn.yml"  # "envs/anacore-sklearn.yml" ################################################
        shell:
            "{params.bin_path}"
            " {params.classifier}"
            " {params.classifier_params}"
            " {params.consensus_method}"
            " {params.instability_ratio}"
            " {params.instability_count}"
            " {params.locus_weight_is_score}"
            " {params.method_name}"
            " {params.min_support}"
            " {params.random_seed}"
            " {params.undetermined_weight}"
            " --input-evaluated {input.evaluated}"
            " --input-model {input.model}"
            " --output-report {output}"
            " {params.stderr_redirection} {log}"
