# GitLab Pipelines

A small collection of templates to make GitLab pipelines easier, especially
when dealing with Spack.

Currently, the following templates are provided:

* `bbp-gitlab-access.yml` to configure accessing BBP GitLab using CI jobs'
  ephemeral tokens.
* `github-project-pipelines.gitlab-ci.yml` sensible defaults for GitHub
  projects.
* `spack-build.gitlab-ci.yml` to build software with Spack.
* `spack-build-ctest.gitlab-ci.yml` to build software with Spack and run
  CTest on it.
* `spack-build-components.gitlab-ci.yml` to build more complicated pipelines
  using Spack and CTest.
* `tox-nse.gitlab-ci.yml` to build a python package with tox following NSE
  practices
* `tox-nse-docs.gitlab-ci.yml` to build as above, but with documentation
  generation and upload enabled

## Configuration

The following variables are used in the template:

* `SPACK_PACKAGE` (required): the package to use when building with Spack.
  Will be used as `${SPACK_PACKAGE}`.
* `SPACK_PACKAGE_COMPILER` (optional): compiler for Spack to use. If this is
  set then the leading `%` will be added automatically.
* `SPACK_PACKAGE_DEPENDENCIES` (optional): additions to the dependencies part
   of the Spack spec. You should include the leading `^` if you set this.
* `SPACK_PACKAGE_SPEC` (optional): additions to the Spack spec when building.
  Will be used as `${SPACK_PACKAGE} ${SPACK_PACKAGE_SPEC}...`.
* `{upper_case_package_name}_{TAG,COMMIT,BRANCH}` (optional): if these are set
  then the `.spack-setup` job passes them to `spack configure-pipeline`, which
  modifies recipes accordingly. These would typically be set by `CI_BRANCHES`
  expressions in GitHub pull request descriptions, when triggering child
  pipelines, or manually when launching a pipeline. If the `_BRANCH` and `_TAG`
  variants are used then these will be resolved to commits in the
  `.spack_setup` job and the corresponding `_COMMIT` variable will be set. Note
  that you will almost certainly want to set `PACKAGE1_COMMIT=${CI_COMMIT_SHA}`
  in any CI plan for "package1" that you build using
  `spack-build-components.gitlab-ci.yml`. If you use
  `spack-build.gitlab-ci.yml` or `spack-build-ctest.gitlab-ci.yml` then this
  will be set automatically based on `${SPACK_PACKAGE}`. Empty values will be
  ignored, which means that the preferred version of that package will be used.
* `SPACK_BRANCH` (optional, only for spack_setup): which branch of Spack to
  use.
* `SPACK_ENV_FILE_URL` (optional, only for spack_setup): an artifact URL to
  download using the GitLab API before setting up Spack. This would typically
  be set to `$SPACK_SETUP_COMMIT_MAPPING_URL` when triggering a child pipeline
  in a different project to ensure that the two pipelines use consistent
  versions. This cannot be set at the same time as
  `PARSE_GITHUB_PR_DESCRIPTIONS="true"`.
* `SPACK_SETUP_IGNORE_PACKAGE_VARIABLES` (optional, only for spack_setup): a
  whitespace-separated list of package names that should be ignored if branch,
  commit or tag variables appear in the environment. For example, if you add
  `BLUECONFIGS` to this list, `BLUECONFIGS_BRANCH` will be ignored if it is set
  in the environment.
* `SPACK_SETUP_COMMIT_MAPPING_URL` (output by spack_setup): the GitLab
  API URL of an artifact file produced by the `spack_setup` job that contains:
  a `{upper_case_package_name}_COMMIT=hash` line for every package whose recipe
  was modified based on `{upper_case_package_name}_{TAG,COMMIT,BRANCH}`
  variables, a `SPACK_BRANCH=branch` line, and a line setting
  `SPACK_DEPLOYMENT_SUFFIX`. In principle this contains enough information to
  reproduce the same Spack setup in a downstream pipeline, but it does not
  contain any references to paths in the current pipeline working directory.
* `SPACK_INSTALL_EXTRA_FLAGS` (optional, debug): these arguments are passed to
  the install command as `spack ${SPACK_INSTALL_EXTRA_FLAGS} install ...`. It
  may be useful to set this to `--debug`, `-ddd` etc. when manually launching a
  problematic pipeline.
* `SPACK_EXTRA_MODULES` (optional): list of modules to load before building
  with Spack.
* `SPACK_DEPLOYMENT_SUFFIX` (optional): extra component added to the GPFS path
  of the software deployment on BB5. For example, `pulls/1418` would use the
  deployed software built in the CI of PR 1418 to BlueBrain/spack. Make sure
  that you think about what you are doing if you set this and `SPACK_BRANCH`
  inconsistently.

## Basic Setup

Say you have a project called `MyAwesomeCode`,
which has an equivalent Spack package `my-awesome-code`.
To use these templates in your own GitLab pipeline,
include them and set a variable to inform the template about your package:
```yaml
include:
  - project: hpc/gitlab-pipelines
    file: spack-build.gitlab-ci.yml

variables:
  SPACK_PACKAGE: my-awesome-code
```
This will build the package with Spack, and pass the package build status
from Spack as unit tests to GitLab (in the `build` stage).

To also automatically run CMake tests, include the corresponding template:
```yaml
include:
  - project: hpc/gitlab-pipelines
    file: spack-build-ctest.gitlab-ci.yml

variables:
  SPACK_PACKAGE: my-awesome-code
```
This will work as the prior template, and in addition create a `ctest` job
to run CMake's testing.
The test information from CMake will be stored in GitLab's unit test
overview in the `test` stage.

## Integration Tests

With either template, additional integration tests can be run by extending
the `.spack_test` definition:
```yaml
my_test:
  extends: .spack_test
```
This will by default expect a shell script `.ci/test_my_test.sh`
(where `my_test` corresponds to the job name).

One can override the job script, too:
```yaml
my_test:
  extends: .spack_test
  script:
    - echo "HELLO WORLD"
```

## Multiple build and test steps

If you want to assemble a more complicated pipeline then you may want to
include `spack-build-components.gitlab-ci.yml` directly.
This file doesn't create any jobs by default, it just defines useful templates
that you can inherit from.
For example, your pipeline almost certainly needs to start by setting up Spack:
```yaml
spack_setup:
  extends: .spack_setup_ccache # Enable ccache support in Spack
```
and then you might want to build a package:
```yaml
variables:
  CORENEURON_COMMIT: ${CI_COMMIT_SHA} # assume this pipeline runs on CoreNEURON

build:coreneuron:
  variables:
    SPACK_PACKAGE: coreneuron
    SPACK_PACKAGE_SPEC: +tests
  extends:
    - .spack_build
```
run the CTest suite of that package:
```yaml
test:coreneuron:
  extends:
    - .ctest
  needs: ["build:coreneuron"]
```
and build another package that depends on the first one:
```yaml
variables:
  NEURON_BRANCH: master

build:neuron:
  variables:
    SPACK_PACKAGE: neuron
    SPACK_PACKAGE_SPEC: +coreneuron
  extends:
    - .spack_build
  needs: ["build:coreneuron"]
```

The `.spack_build` template will automatically extract the hash (`deadbeef...`)
describing the first installed package (`coreneuron`) and add it to the Spack
spec of the second package (`neuron`), constructing something like
`spack install neuron+coreneuron^/deadbeef...` that guarantees the
CI build of the second package uses the CI build of the first one.

Note that because in this example `build:neuron` and `test_coreneuron` have
the same dependencies (`needs: ["build:coreneuron"]`) they will execute in
parallel in the pipeline.

## Configuring alternative branches using GitHub pull request keywords

When using GitLab CI with an external GitHub repository, such as BBP's open
source projects, it can be useful to build against specific versions of
dependencies instead of just using the tip of the default branch. To enable
this functionality one can set the `PARSE_GITHUB_PR_DESCRIPTIONS` variable to
the string `"true"` in the environment of the Spack setup job. For example:
```yaml
spack_setup:
  extends: .spack_setup_ccache
  variables:
    # Enable fetching GitHub PR descriptions and parsing them to find out what
    # branches to build of other projects.
    PARSE_GITHUB_PR_DESCRIPTIONS: "true"
```
In this case the `spack_setup` job will query the GitHub API to get information
about the external GitHub pull request and parse its description. The supported
syntax is:
```
CI_BRANCHES:PROJECT1_REFTYPE1=REF1,PROJECT2_REFTYPE2=REF2[,...]
```
at the start of a line in the pull request description. The project name(s)
will be transformed to lower case and should match the package name(s) in
Spack. The `REFTYPE` is case insensitive and may be one of `branch`, `commit`
and `tag`. `REF` is case sensitive. For example:
```
CI_BRANCHES:NEURON_BRANCH=some/feature-branch
```
The variables will be set in the CI job environment and passed to the
`spack configure-pipeline` command.

The branch of Spack that is checked out can be specified using the same syntax,
`CI_BRANCHES:SPACK_BRANCH=some/feature-branch`. In this case only branch
specifications are supported, not tags or commits.

This is a re-implementation of a similar feature in the previous CI setup that
was based on Jenkins.

# Other useful templates

This repository also includes other templates that may be useful when building
CI pipelines.

## bbp-gitlab-access.yml

A common issue is that private BBP software, which is hosted on the BBP GitLab
instance, cannot be cloned from there without authentication.
When running interactively, we typically use URLs such as
```
git@bbpgitlab.epfl.ch:hpc/gitlab-pipelines.git
```
and rely on our personal SSH keys being registered with GitLab.
This does not work in CI jobs, at least those using the recommended `bb5_map`
tag, as there is no relevant SSH key.
One solution to this problem is to use the
[`${CI_JOB_TOKEN}`](https://docs.gitlab.com/ee/ci/jobs/ci_job_token.html)
variable that is provided by GitLab instead of SSH.
The `bbp-gitlab-access.yml` file provides a job template called
`.bbp_gitlab_access` whose `script` block sets `$XDG_CONFIG_HOME` to a
job-unique directory and writes a `git` configuration file that redirects
`git@bbpgitlab.epfl.ch` URLs to use `${CI_JOB_TOKEN}`.
To use this, you should add `bbp-gitlab-access.yml` to an `include:` block in
your YAML file and then do something like:
```yaml
myjob:
  script:
   - !reference [.bbp_gitlab_access, script]
   - git clone git@bbpgitlab.epfl.ch:hpc/gitlab-pipelines.git
```

## github-project-pipelines.gitlab-ci.yml

This repository also includes a template,
`github-project-pipelines.gitlab-ci.yml`, that configures sensible default
behaviour for a GitHub repository that is mirrored to GitLab for CI purposes.
It can be included as follows:
```yaml
include:
  - project: hpc/gitlab-pipelines
    file: github-project-pipelines.gitlab-ci.yml
```
With this configuration the GitLab CI will run every time an update is made to
a pull request on GitHub. It will also run when changes are pushed to the
default branch.
