#!/bin/bash

# Parameters
if [ "$#" -eq 0 ]; then
    echo -e "[\033[0;31mERROR\033[0m] The working directory must be provided: $0 CONDA_ENVS_DIR WORK_DIR 'DRMAA_params'"
    exit 1
elif [ "$#" -ne 3 ] && [ "$#" -ne 4 ]; then
    echo -e "[\033[0;31mERROR\033[0m] Illegal number of parameters"
    exit 1
fi
conda_envs_dir=$1
work_dir=$2
DRMAA_params=$3
nb_threads=2
if [ "$#" -eq 4 ]; then
    nb_threads=$4
fi
test_dir=`dirname $0`
test_dir=`realpath ${test_dir}`
application_dir=`dirname ${test_dir}`

# Process
mkdir -p ${work_dir} && \
cp -r ${application_dir}/test/raw ${work_dir}/raw && \
cp -r ${application_dir}/test/config ${work_dir}/config && \
snakemake \
  --use-conda \
  --conda-prefix ${conda_envs_dir} \
  --jobs ${nb_threads} \
  --jobname "miniti.{rule}.{jobid}" \
  --latency-wait 200 \
  --cluster-config ${application_dir}/config/cluster.json \
  --drmaa "${DRMAA_params}" \
  --snakefile ${application_dir}/Snakefile \
  --configfile ${work_dir}/config/wf_config.yml \
  --directory ${work_dir} \
  2> ${work_dir}/wf_stderr.txt

# Check execution
if [ $? -ne 0 ]; then
    echo -e "[\033[0;31mERROR\033[0m] Workflow execution error (log: ${work_dir}/wf_stderr.txt)"
    exit 1
fi
echo "Workflow execution success"
