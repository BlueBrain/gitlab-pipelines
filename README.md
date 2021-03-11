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
   of the Spack spec. If this is set the leading `^` will be added
   automatically.
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

## Basic Setup

Say you have a project called `MyAwesomeCode`,
which has an equivalent Spack package `my-awesome-code`.
To use these templates in your own GitLab pipeline,
include them and set a variable to inform the template about your 
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