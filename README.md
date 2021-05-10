# GitLab Pipelines

A small collection of templates to make GitLab pipelines easier, especially
when dealing with Spack.

Currently, the following templates are provided:

* `spack-build.gitlab-ci.yml` to build software with Spack.
* `spack-build-ctest.gitlab-ci.yml` to build software with Spack and run
  CTest on it.
* `spack-build-components.gitlab-ci.yml` to build more complicated pipelines using Spack and CTest.

## Configuration

The following variables are used in the template:

* `SPACK_PACKAGE` (required): the package to use when building with Spack.
  Will be used as `${SPACK_PACKAGE}@develop`.
* `SPACK_PACKAGE_COMPILER` (optional): compiler for Spack to use. If this is
  set the leading `%` will be added automatically.
* `SPACK_PACKAGE_DEPENDENCIES` (optional): additions to the dependencies part
   of the Spack spec. You should include the leading `^` if you set this.
* `SPACK_PACKAGE_REF` (optional): which git commit/tag/branch to checkout when
  building the package. By default the git commit (`${CI_COMMIT_SHA}`) the
  pipeline is running on is used. If this is set to a non-empty string then any
  existing `tag`, `commit` or `branch` keyword argument is removed from the
  Spack recipe and this is inserted as
  `version("develop", ${SPACK_PACKAGE_REF} ...)` so it should be of the form
  `commit="sha.."`, `tag="tag_name"` or `branch="branch_name"`.
* `SPACK_PACKAGE_SPEC` (optional): additions to the Spack spec when building.
  Will be used as `${SPACK_PACKAGE}@develop${SPACK_PACKAGE_SPEC}...`.
* `SPACK_BRANCH` (optional, only for spack_setup): which branch of Spack to
  use.
* `SPACK_EXPORT_SPECS` (optional, discouraged): a list of Spack specs that will
  be added to a build-step-local `packages.yaml` as external packages. This can
  be used to encourage Spack not to rebuild too much of the world, in
  particular if you are trying to build with a nonstandard compiler or compiler
  version. Passed to `spack export --scope=user --module tcl --explicit`.
* `SPACK_INSTALL_EXTRA_FLAGS` (optional, debug): these arguments are passed to
  the install command as `spack ${SPACK_INSTALL_EXTRA_FLAGS} install ...`. It
  may be useful to set this to `--debug`, `-ddd` etc. when manually launching a
  problematic pipeline.

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
  extends: .spack_setup_ccache # Enable ccache support in Spack (incomplete!)
```
and then you might want to build a package:
```yaml
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
build:neuron:
  stage: build_neuron # we extended the standard .pre/build/test/.post
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
`spack install neuron@develop+coreneuron^/deadbeef...` that guarantees the
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
Note that these requests will only be honoured for packages that have explicit
build steps in the pipeline. For example, in the above example with CoreNEURON
and NEURON that runs in the CI for CoreNEURON then:
- `CI_BRANCHES:NEURON_BRANCH=some/feature-branch` makes sense and should work
- `CI_BRANCHES:CORENEURON_BRANCH=some/feature-branch` is nonsensical, you would
  be running a CI pipeline attached to a particular ref in CoreNEURON that
  builds and tests a different ref in CoreNEURON. That said, it will silently
  build the specified branch and override the default `${CI_COMMIT_SHA}`.
- `CI_BRANCHES:BISON_TAG=v3.0.6` will be silently ignored, CoreNEURON depends
  on `bison` but there is no explicit build step for `bison`.

This is a re-implementation of a similar feature in the previous CI setup that
was based on Jenkins.

# Other useful templates

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

# Limitations

This section lists a few known limitations of the templates.
- `SPACK_PACKAGE_DEPENDENCIES` is overriden by the output artifacts of build
  steps. This means if you are building `library` and `application` (that
  depends on `library`) in your pipeline then setting
  `SPACK_PACKAGE_DEPENDENCIES` explicitly on `application` will have no effect;
  it will be overwritten by some `^/hash_of_library_installation` from `library`
- All build jobs share one Spack installation, this means that if you have
  multiple build jobs for the same package then they will all try and modify
  the same recipe (`package.py`). This is probably OK unless the build steps
  have different `SPACK_PACKAGE_REF` values; in that case you should use
  `needs` relationships to avoid the builds running in parallel.