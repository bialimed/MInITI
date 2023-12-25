#!/bin/bash
wf=$1
config=$2
out=$3

assessment_bin_dir=`dirname $0`
assessment_bin_dir=`realpath ${assessment_bin_dir}`
assessment_dir=`dirname ${assessment_bin_dir}`
application_dir=`dirname ${assessment_dir}`

unset PYTHONPATH && \
source /Anapath/soft/conda/current/bin/activate miniti && \
snakemake \
--printshellcmds \
--jobs 100 \
--latency-wait 240 \
--restart-times 2 \
--cluster "sbatch --partition={resources.partition} --mem={resources.mem} --cpus-per-task={threads}" \
--use-conda --conda-prefix /Anapath/soft/conda/current/envs \
--snakefile ${application_dir}/$wf \
--configfile $config \
--directory $out \
> $out/wf_log.txt \
2> $out/wf_stderr.txt
