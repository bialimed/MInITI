__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2022 CHU-Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'

#msisensor-pro scan -d /Anapath/bank/Homo_sapiens/DNA/GRCh38_Ensembl101/sequences/Homo_sapiens.GRCh38.ensembl_v101.dna.toplevel.chrOnly.fa -o scan_out.txt
#msisensor-pro baseline -d scan_out_targeted.txt -i cfg_baseline.txt -c 50 -o baseline_out_targeted
#msisensor-pro pro -d baseline_out_targeted/scan_out_targeted.txt_baseline -t ../miniti/assessment/datasets/solid_tumor_v3/aln/22T017864.bam -o pro_out_targeted_22T017864
include: "msisensorpro_pro.smk"

def microsatMsisensorproProClassify(
        in_alignments="aln/{sample}.bam",
        in_microsatellites="design/microsat.bed",
        in_model="microsat/microsatModel.json",
        in_sequences="data/reference.fa",
        out_baseline="microsat/msisensorpro/baseline.tsv",
        out_report="microsat/msisensorpro/{sample}_stabilityStatus.json",
        params_flank_size=None,
        params_instability_ratio=None,
        params_locus_weight_is_score=None,
        params_min_depth=None,
        params_min_voting_loci=None,
        params_model_method_name=None,
        params_sample_name="{sample}",
        params_undetermined_weight=None,
        params_keep_outputs=False,
        params_stderr_append=False):
    """Predict stability classes and scores for loci and samples using MSIsensor-pro."""
    rule modelToBaseline:
        input:
            microsatellites = in_microsatellites,
            model = in_model,
            sequences = in_sequences
        output:
            out_baseline if params_keep_outputs else temp(out_baseline)
        log:
            out_stderr
        params:
            bin_path = os.path.abspath(os.path.join(workflow.basedir, "scripts/modelToBaseline.py")),
            flank_size = "" if params_flank_size is None else "--flank-size {}".format(params_flank_size),
            method_name = "" if params_model_method_name is None else "--method-name {}".format(params_model_method_name),
            stderr_redirection = "2>" if not params_stderr_append else "2>>",
        conda:
            "envs/anacore.yml"
        shell:
            "{params.bin_path}"
            " {params.flank_size}"
            " {params.method_name}"
            " --input-models {input.models}"
            " --input-sequences {input.sequences}"
            " --input-targets {input.targets}"
            " --output-baseline {output}"
            " {params.stderr_redirection} {log}"

    mssisensorpro_pro(
        in_alignments="aln/{sample}.bam",
        in_baseline=out_baseline,
        out_distrib=out_report + "_tmp_distrib.tsv",
        out_loci=out_report + "_tmp_loci.tsv",
        out_status=out_report + "_tmp_status.tsv",
        out_unstable=out_report + "_tmp_unstable.txt",
        out_stderr=out_stderr + "_MSIsensorProPro_stderr.txt",
        params_min_depth=params_min_depth
    )

    rule msisensorproProToReport:
        input:
            distributions = out_report + "_tmp_distrib.tsv",
            loci = out_report + "_tmp_loci.tsv"
        output:
            out_report if params_keep_outputs else temp(out_report)
        log:
            out_stderr
        params:
            bin_path = os.path.abspath(os.path.join(workflow.basedir, "scripts/msisensorproProToReport.py")),
            instability_ratio = "" if params_instability_ratio else "--instability-ratio {}".format(params_instability_ratio),
            locus_weight_is_score = "" if params_locus_weight_is_score is None else "--locus-weight-is-score",
            min_depth = "" if params_min_depth is None else "-c {}".format(params_min_depth),
            min_voting_loci = "" if params_min_voting_loci is None else "--min-voting-loci {}".format(params_min_voting_loci),
            sample_name = "" if params_sample_name is None else "--sample-name {}".format(params_sample_name),
            stderr_redirection = "2>" if not params_stderr_append else "2>>",
            undetermined_weight = "" if params_undetermined_weight is None else "--undetermined-weight {}".format(params_undetermined_weight)
        conda:
            "envs/anacore-utils.yml"
        shell:
            "{params.bin_path}"
            " {params.instability_ratio}"
            " {params.locus_weight_is_score}"
            " {params.min_depth}"
            " {params.min_voting_loci}"
            " {params.sample_name}"
            " {params.undetermined_weight}"
            " --input-distributions {input.distributions}"
            " --input-loci {input.loci}"
            " --output-report {output}"
            " {params.stderr_redirection} {log}"
