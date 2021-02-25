# GitLab Pipelines

A small collection of templates to make GitLab pipelines easier, especially
when dealing with Spack.

Currently, the following templates are provided:

* `spack-build.gitlab-ci.yml` to build software with Spack
* `spack-build-ctest.gitlab-ci.yml` to build software with Spack and run
  CTest on it.

## Configuration

The following variables are used in the template:

* `SPACK_PACKAGE` (required): the package to use when building with Spack.
  Will be used as `${SPACK_PACKAGE}@develop`.
* `SPACK_SPEC` (optional): additions to the Spack spec when building.
  Will be used as `${SPACK_PACKAGE}@develop${SPACK_SPEC}`.

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
