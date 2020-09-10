# MInITI: Microsatellites INstability from hIgh Throughput sequencIng

![license](https://img.shields.io/badge/license-GPLv3-blue)

## Description
This workflow classify microsatellites instability from high througput
sequencing on Illumina's instruments.

## Workflow steps
TODO

## Installation
### 1. Download code
Use one of the following:

* [user way] Downloads the latest released versions from
`https://bitbucket.org/fescudie/miniti/downloads/?tab=tags`.
* [developper way] Clones the repository from the latest unreleased version:

      git clone https://bitbucket.org/fescudie/miniti.git

### 2. Install dependencies
* conda (>=4.6.8):

      wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
      sh Miniconda3-latest-Linux-x86_64.sh

  More details on miniconda install [here](https://docs.conda.io/en/latest/miniconda.html).

* snakemake (>=5.4.2):

      conda install snakemake

  More details on snakemake install [here](https://snakemake.readthedocs.io/en/stable/getting_started/installation.html).

The others dependencies (cutadapt, bwa, ...) will be automatically installed by
snakemake at the first execution. This first execution required an access to
internet.

### 4. Download and prepare resources
TODO

### 3. Test install
TODO

## Usage
Copy `${application_dir}/config/config_tag_tpl.yml` in your current
directory and change values before launching the following command:

    snakemake \
      --use-conda \
      --conda-prefix ${application_env_dir} \
      --jobs ${nb_jobs} \
      --latency-wait 100 \
      --snakefile ${application_dir}/Snakefile_tag \
      --cluster-config ${application_dir}/config/cluster.json \
      --configfile config_tag.yml \
      --directory ${out_dir} \
      > ${out_dir}/wf_log.txt \
      2> ${out_dir}/wf_stderr.txt

## Outputs directory
The main elements of the outputs directory are the following:

    out_dir/
    ├── ...
    └── report/
        ├── ...
        ├── run.html
        └── sample-A.html


TODO

## Performances
TODO

## Copyright
2020 Laboratoire d'Anatomo-Cytopathologie de l'Institut Universitaire du Cancer
Toulouse - Oncopole

## Contact
escudie.frederic@iuct-oncopole.fr
