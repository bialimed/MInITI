__author__ = 'Frederic Escudie'
__copyright__ = 'Copyright (C) 2022 CHU-Toulouse'
__license__ = 'GNU General Public License'
__version__ = '1.0.0'


def msisensorpro_pro(
        in_alignments="aln/{sample}.bam",
        in_baseline="microsat/msisensorpro/baseline.txt",
        out_distrib="microsat/msisensorpro/{sample}_distrib.txt",
        out_loci="microsat/msisensorpro/{sample}_loci.tsv",
        out_status="microsat/msisensorpro/{sample}_status.tsv",
        out_unstable="microsat/msisensorpro/{sample}_unstable.txt",
        out_stderr="logs/{sample}_MSIsensorProPro_stderr.txt",
        params_min_depth=None,
        params_keep_outputs=False,
        params_stderr_append=False):
    """Predict stability classes and scores for loci and samples using MSIsensor-pro."""
    tmp_prefix = out_status + "_tmp"
    rule msisensorpro_pro:
        input:
            alignments = in_alignments,
            baseline = in_baseline
        output:
            out_distrib if params_keep_outputs else temp(out_distrib),
            out_loci if params_keep_outputs else temp(out_loci),
            out_status if params_keep_outputs else temp(out_status),
            out_unstable if params_keep_outputs else temp(out_unstable)
        log:
            out_stderr
        params:
            bin_path = config.get("software_paths", {}).get("msisensor-pro", "msisensor-pro"),
            min_depth = "" if params_min_depth is None else "-c {}".format(params_min_depth),
            prefix = tmp_prefix,
            stderr_redirection = "2>" if not params_stderr_append else "2>>",
        conda:
            "envs/msisensor-pro.yml"
        shell:
            "{params.bin_path} pro"
            " -0"
            " {params.min_depth}"
            " -d {input.baseline}"
            " -t {input.alignments}"
            " -o {params.prefix}"
            " {params.stderr_redirection} {log}"
            " && "
            "mv {params.prefix} {output.status} 2>> {log}"
            " && "
            "mv {params.prefix}_all {output.loci} 2>> {log}"
            " && "
            "mv {params.prefix}_dis {output.distrib} 2>> {log}"
            " && "
            "mv {params.prefix}_unstable {output.unstable} 2>> {log}"
