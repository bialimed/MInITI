#!/bin/bash
wf=$1
config=$2
out=$3

assessment_bin_dir=`dirname $0`
assessment_bin_dir=`realpath ${assessment_bin_dir}`
assessment_dir=`dirname ${assessment_bin_dir}`
application_dir=`dirname ${assessment_dir}`

unset PYTHONPATH && \
source /labos/Anapath/soft/conda/current/bin/activate miniti && \
snakemake \
--printshellcmds \
--jobs 40 \
--jobname "miniti.eval.{rule}.{jobid}" \
--latency-wait 240 \
--restart-times 1 \
--max-jobs-per-second 1 \
--max-status-checks-per-second 1 \
--cluster "sbatch --partition=normal --mem={resources.mem} --cpus-per-task={threads}" \
--use-conda --conda-prefix /labos/Anapath/soft/conda/current/envs \
--snakefile ${application_dir}/$wf \
--configfile $config \
--directory $out \
> $out/wf_log.txt \
2> $out/wf_stderr.txt
