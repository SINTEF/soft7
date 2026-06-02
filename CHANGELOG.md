# Changelog

## [Unreleased](https://github.com/SINTEF/soft7/tree/HEAD)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.5.0...HEAD)

## Use `httpx2`

Starlette (the underlying framework used by FastAPI) have started to rely on [HTTPX2](https://httpx2.pydantic.dev). This seems like a good choice to move to, since it is a fork of HTTPX and will be maintained by the Pydantic team.

This has required the update from `pytest-httpx` to `httpx2-pytest` as well. The latter being a fork of the former, but supporting HTTPX2.

## Miscellaneous

Updated GitHub Actions, development tools, and minimum expected requirements.

**Closed issues:**

- Use HTTPX2 [\#184](https://github.com/SINTEF/soft7/issues/184)

## [v0.5.0](https://github.com/SINTEF/soft7/tree/v0.5.0) (2026-06-02)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.4.0...v0.5.0)

## Use `httpx2`

Starlette (the underlying framework used by FastAPI) have started to rely on [HTTPX2](https://httpx2.pydantic.dev). This seems like a good choice to move to, since it is a fork of HTTPX and will be maintained by the Pydantic team.

This has required the update from `pytest-httpx` to `httpx2-pytest` as well. The latter being a fork of the former, but supporting HTTPX2.

## Miscellaneous

Updated GitHub Actions, development tools, and minimum expected requirements.

**Merged pull requests:**

- Update HTTPX -\> HTTPX2 [\#185](https://github.com/SINTEF/soft7/pull/185) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#183](https://github.com/SINTEF/soft7/pull/183) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#182](https://github.com/SINTEF/soft7/pull/182) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update pydata-sphinx-theme requirement from ~=0.17.0 to \>=0.17,\<0.19 in the packages group across 1 directory [\#181](https://github.com/SINTEF/soft7/pull/181) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#180](https://github.com/SINTEF/soft7/pull/180) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#179](https://github.com/SINTEF/soft7/pull/179) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#178](https://github.com/SINTEF/soft7/pull/178) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump the actions group with 2 updates [\#177](https://github.com/SINTEF/soft7/pull/177) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#176](https://github.com/SINTEF/soft7/pull/176) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump actions/upload-pages-artifact from 4 to 5 in the actions group [\#175](https://github.com/SINTEF/soft7/pull/175) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#174](https://github.com/SINTEF/soft7/pull/174) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump actions/github-script from 8 to 9 in the actions group [\#173](https://github.com/SINTEF/soft7/pull/173) ([dependabot[bot]](https://github.com/apps/dependabot))
- Update pydata-sphinx-theme requirement from ~=0.16.1 to \>=0.16.1,\<0.18.0 in the packages group across 1 directory [\#172](https://github.com/SINTEF/soft7/pull/172) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#171](https://github.com/SINTEF/soft7/pull/171) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump the actions group across 1 directory with 2 updates [\#170](https://github.com/SINTEF/soft7/pull/170) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump actions/deploy-pages from 4 to 5 in the actions group [\#168](https://github.com/SINTEF/soft7/pull/168) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#167](https://github.com/SINTEF/soft7/pull/167) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#166](https://github.com/SINTEF/soft7/pull/166) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#165](https://github.com/SINTEF/soft7/pull/165) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#164](https://github.com/SINTEF/soft7/pull/164) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump actions/download-artifact from 7 to 8 in the actions group [\#163](https://github.com/SINTEF/soft7/pull/163) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#162](https://github.com/SINTEF/soft7/pull/162) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#161](https://github.com/SINTEF/soft7/pull/161) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump pip-tools from 7.5.2 to 7.5.3 in /.github/utils in the packages group across 1 directory [\#160](https://github.com/SINTEF/soft7/pull/160) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#159](https://github.com/SINTEF/soft7/pull/159) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#158](https://github.com/SINTEF/soft7/pull/158) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#157](https://github.com/SINTEF/soft7/pull/157) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#156](https://github.com/SINTEF/soft7/pull/156) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#155](https://github.com/SINTEF/soft7/pull/155) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#154](https://github.com/SINTEF/soft7/pull/154) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump actions/download-artifact from 6 to 7 in the actions group [\#153](https://github.com/SINTEF/soft7/pull/153) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#152](https://github.com/SINTEF/soft7/pull/152) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update pytest-httpx requirement from ~=0.35.0 to \>=0.35,\<0.37 in the packages group across 1 directory [\#151](https://github.com/SINTEF/soft7/pull/151) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#150](https://github.com/SINTEF/soft7/pull/150) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#149](https://github.com/SINTEF/soft7/pull/149) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump the packages group across 1 directory with 2 updates [\#148](https://github.com/SINTEF/soft7/pull/148) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump actions/checkout from 5 to 6 in the actions group [\#147](https://github.com/SINTEF/soft7/pull/147) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#146](https://github.com/SINTEF/soft7/pull/146) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#145](https://github.com/SINTEF/soft7/pull/145) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump the packages group across 2 directories with 2 updates [\#144](https://github.com/SINTEF/soft7/pull/144) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump actions/download-artifact from 5 to 6 in the actions group [\#143](https://github.com/SINTEF/soft7/pull/143) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#142](https://github.com/SINTEF/soft7/pull/142) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#141](https://github.com/SINTEF/soft7/pull/141) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#140](https://github.com/SINTEF/soft7/pull/140) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#139](https://github.com/SINTEF/soft7/pull/139) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#138](https://github.com/SINTEF/soft7/pull/138) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update pytest-cov requirement from ~=6.1 to \>=6.1,\<8.0 in the packages group [\#137](https://github.com/SINTEF/soft7/pull/137) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#136](https://github.com/SINTEF/soft7/pull/136) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump actions/github-script from 7 to 8 in the actions group [\#135](https://github.com/SINTEF/soft7/pull/135) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump actions/setup-python from 5 to 6 in the actions group [\#134](https://github.com/SINTEF/soft7/pull/134) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#133](https://github.com/SINTEF/soft7/pull/133) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump actions/upload-pages-artifact from 3 to 4 in the actions group [\#132](https://github.com/SINTEF/soft7/pull/132) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#131](https://github.com/SINTEF/soft7/pull/131) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#130](https://github.com/SINTEF/soft7/pull/130) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump actions/checkout from 4 to 5 in the actions group [\#129](https://github.com/SINTEF/soft7/pull/129) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#128](https://github.com/SINTEF/soft7/pull/128) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump actions/download-artifact from 4 to 5 in the actions group [\#127](https://github.com/SINTEF/soft7/pull/127) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#126](https://github.com/SINTEF/soft7/pull/126) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#125](https://github.com/SINTEF/soft7/pull/125) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#124](https://github.com/SINTEF/soft7/pull/124) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#123](https://github.com/SINTEF/soft7/pull/123) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#122](https://github.com/SINTEF/soft7/pull/122) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#121](https://github.com/SINTEF/soft7/pull/121) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#120](https://github.com/SINTEF/soft7/pull/120) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#119](https://github.com/SINTEF/soft7/pull/119) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#118](https://github.com/SINTEF/soft7/pull/118) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#117](https://github.com/SINTEF/soft7/pull/117) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#116](https://github.com/SINTEF/soft7/pull/116) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#115](https://github.com/SINTEF/soft7/pull/115) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Drop safety in favor of pip-audit [\#114](https://github.com/SINTEF/soft7/pull/114) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#113](https://github.com/SINTEF/soft7/pull/113) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.4.0](https://github.com/SINTEF/soft7/tree/v0.4.0) (2025-04-11)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.3.1...v0.4.0)

# Drop Python 3.9 & support OTE v1

This release drops Python 3.9 support.
This is in trend with the support for OTEAPI Core and OTELib v1, which has recently been released. These have also dropped Python 3.9 support.

## Remove AllegroGraph from the Docker Compose file

AllegroGraph as well as the accompanying configuration file has been removed from the Docker Compose file.

## DX

The dev tools have been updated and `markdownlint-cli2` and `blacken-docs` have been added.
The code base has been updated after upping the minimum version for pyupgrade to 3.10.

**Implemented enhancements:**

- Upgrade to OTE v1 [\#110](https://github.com/SINTEF/soft7/issues/110)

**Closed issues:**

- Drop Python 3.9 [\#111](https://github.com/SINTEF/soft7/issues/111)

**Merged pull requests:**

- Use non-dev OTE versions [\#109](https://github.com/SINTEF/soft7/pull/109) ([CasperWA](https://github.com/CasperWA))

## [v0.3.1](https://github.com/SINTEF/soft7/tree/v0.3.1) (2025-04-08)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.3.0...v0.3.1)

## Update core dependencies

Specifically, this patch update is for supporting the latest pydantic v2.11, which deprecates certain attributes, when accessing them from instances.

### DX

Developer tools and GitHub Actions have also been updated.

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#107](https://github.com/SINTEF/soft7/pull/107) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#106](https://github.com/SINTEF/soft7/pull/106) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#105](https://github.com/SINTEF/soft7/pull/105) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#104](https://github.com/SINTEF/soft7/pull/104) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump SINTEF/ci-cd from 2.9.1 to 2.9.2 in the actions group [\#103](https://github.com/SINTEF/soft7/pull/103) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#102](https://github.com/SINTEF/soft7/pull/102) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#101](https://github.com/SINTEF/soft7/pull/101) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump SINTEF/ci-cd from 2.9.0 to 2.9.1 in the actions group [\#100](https://github.com/SINTEF/soft7/pull/100) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#99](https://github.com/SINTEF/soft7/pull/99) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#98](https://github.com/SINTEF/soft7/pull/98) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#97](https://github.com/SINTEF/soft7/pull/97) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#96](https://github.com/SINTEF/soft7/pull/96) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump SINTEF/ci-cd from 2.8.3 to 2.9.0 in the actions group [\#95](https://github.com/SINTEF/soft7/pull/95) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#94](https://github.com/SINTEF/soft7/pull/94) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#93](https://github.com/SINTEF/soft7/pull/93) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#92](https://github.com/SINTEF/soft7/pull/92) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#91](https://github.com/SINTEF/soft7/pull/91) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#90](https://github.com/SINTEF/soft7/pull/90) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#89](https://github.com/SINTEF/soft7/pull/89) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.3.0](https://github.com/SINTEF/soft7/tree/v0.3.0) (2024-12-02)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.2.2...v0.3.0)

# New `graph` module

Perform RDF graph operations, specifically meant for usage with SOFT7 and semantic interoperability utilizing the `s7.graph` module.

The main underlying technology is [RDFLib](https://rdflib.readthedocs.io/) and [SPARQLWrapper](https://sparqlwrapper.readthedocs.io/).

## Support Python 3.13

CI tests and official package metadata support for Python 3.13 has been added.

## Support Pydantic v2.10

There were several changes to the networking models in pydantic v2.10 - this update remedies most of these changes.

**Implemented enhancements:**

- Test support for Python 3.13 [\#71](https://github.com/SINTEF/soft7/issues/71)

**Merged pull requests:**

- Bump the dependencies group with 2 updates [\#87](https://github.com/SINTEF/soft7/pull/87) ([dependabot[bot]](https://github.com/apps/dependabot))
- Move in graphs to s7 package [\#86](https://github.com/SINTEF/soft7/pull/86) ([CasperWA](https://github.com/CasperWA))
- Test with Python 3.13 [\#85](https://github.com/SINTEF/soft7/pull/85) ([CasperWA](https://github.com/CasperWA))

## [v0.2.2](https://github.com/SINTEF/soft7/tree/v0.2.2) (2024-11-25)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.2.1...v0.2.2)

# Fix issue with pydantic v2.10

There are some issues with pydantic's v2.10 concerning `Url` models.
Since we use the pydantic version specified by `oteapi-core`, we make sure to at least use v0.7.0.dev6, since this ensure v2.10.0 and v2.10.1 is not installed.
When v2.10.2 comes out, it can be tested on `oteapi-core` before a new release is done.

All other dependencies and dev tools have also been updated.

**Merged pull requests:**

- Update pytest-httpx requirement from ~=0.33.0 to \>=0.33,\<0.35 in the dependencies group [\#82](https://github.com/SINTEF/soft7/pull/82) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#81](https://github.com/SINTEF/soft7/pull/81) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump codecov/codecov-action from 4 to 5 in the actions group [\#80](https://github.com/SINTEF/soft7/pull/80) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#79](https://github.com/SINTEF/soft7/pull/79) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#78](https://github.com/SINTEF/soft7/pull/78) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump the dependencies group with 2 updates [\#77](https://github.com/SINTEF/soft7/pull/77) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#76](https://github.com/SINTEF/soft7/pull/76) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update pydata-sphinx-theme requirement from ~=0.15.2 to \>=0.15.2,\<0.17.0 in the dependencies group [\#75](https://github.com/SINTEF/soft7/pull/75) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#74](https://github.com/SINTEF/soft7/pull/74) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump SINTEF/ci-cd from 2.8.2 to 2.8.3 in the actions group [\#73](https://github.com/SINTEF/soft7/pull/73) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#72](https://github.com/SINTEF/soft7/pull/72) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#70](https://github.com/SINTEF/soft7/pull/70) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update pre-commit requirement from ~=3.7 to ~=4.0 in the dependencies group [\#69](https://github.com/SINTEF/soft7/pull/69) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#68](https://github.com/SINTEF/soft7/pull/68) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update pytest-httpx requirement from ~=0.31.1 to ~=0.32.0 in the dependencies group [\#67](https://github.com/SINTEF/soft7/pull/67) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#66](https://github.com/SINTEF/soft7/pull/66) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update pytest-httpx requirement from ~=0.30.0 to \>=0.30,\<0.32 in the dependencies group [\#65](https://github.com/SINTEF/soft7/pull/65) ([dependabot[bot]](https://github.com/apps/dependabot))

## [v0.2.1](https://github.com/SINTEF/soft7/tree/v0.2.1) (2024-09-18)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.2.0...v0.2.1)

## Remove upper limit for `oteapi-core` dependency

While not recommended, this does make it possible to support the DataSpaces developed at SINTEF.
In the future a more stringent dependency tree/graph should be implemented for all packages.

**Fixed bugs:**

- Update example OpenAPI specs [\#61](https://github.com/SINTEF/soft7/issues/61)
- Fix deployment issue [\#57](https://github.com/SINTEF/soft7/issues/57)

**Merged pull requests:**

- Remove upper level version dependency for `oteapi-core` [\#62](https://github.com/SINTEF/soft7/pull/62) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#60](https://github.com/SINTEF/soft7/pull/60) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#59](https://github.com/SINTEF/soft7/pull/59) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Ensure CI jobs are run for push-protected action branches [\#58](https://github.com/SINTEF/soft7/pull/58) ([CasperWA](https://github.com/CasperWA))

## [v0.2.0](https://github.com/SINTEF/soft7/tree/v0.2.0) (2024-08-27)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.1.0...v0.2.0)

## Support different SOFT flavors

Implement support for different SOFT flavors, specifically, support the [DLite](https://github.com/SINTEF/dlite) flavor of SOFT entities.

### DX

Update dev tools and use [PyPIs Trusted Publishers](https://docs.pypi.org/trusted-publishers/) scheme.

**Implemented enhancements:**

- Unify SOFT7 datamodels with DLite datamodels [\#7](https://github.com/SINTEF/soft7/issues/7)

**Closed issues:**

- Update release workflow to support PyPI's Trusted Publishers [\#42](https://github.com/SINTEF/soft7/issues/42)
- Add `skip-changelog` label to bot-PRs [\#41](https://github.com/SINTEF/soft7/issues/41)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#55](https://github.com/SINTEF/soft7/pull/55) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Bump SINTEF/ci-cd from 2.8.0 to 2.8.2 in the actions group [\#54](https://github.com/SINTEF/soft7/pull/54) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#53](https://github.com/SINTEF/soft7/pull/53) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Implement validators to handle different SOFT entity flavors [\#51](https://github.com/SINTEF/soft7/pull/51) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#50](https://github.com/SINTEF/soft7/pull/50) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#49](https://github.com/SINTEF/soft7/pull/49) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update sphinx requirement from ~=7.3 to \>=7.3,\<9.0 in the dependencies group [\#48](https://github.com/SINTEF/soft7/pull/48) ([dependabot[bot]](https://github.com/apps/dependabot))
- Bump actions/github-script from 5 to 7 in the actions group [\#47](https://github.com/SINTEF/soft7/pull/47) ([dependabot[bot]](https://github.com/apps/dependabot))
- \[pre-commit.ci\] pre-commit autoupdate [\#46](https://github.com/SINTEF/soft7/pull/46) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Ensure 'skip-changelog' label is added for \[bot\] PRs [\#45](https://github.com/SINTEF/soft7/pull/45) ([CasperWA](https://github.com/CasperWA))
- \[pre-commit.ci\] pre-commit autoupdate [\#44](https://github.com/SINTEF/soft7/pull/44) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Use PyPI's Trusted Publisher feature [\#43](https://github.com/SINTEF/soft7/pull/43) ([CasperWA](https://github.com/CasperWA))

## [v0.1.0](https://github.com/SINTEF/soft7/tree/v0.1.0) (2024-07-12)

[Full Changelog](https://github.com/SINTEF/soft7/compare/2ffa953762f8a6a2766ffb7946afadadbb0a687b...v0.1.0)

**Implemented enhancements:**

- Use pydantic v2 [\#12](https://github.com/SINTEF/soft7/issues/12)
- Write up unit tests [\#11](https://github.com/SINTEF/soft7/issues/11)
- Setup development helping tools [\#9](https://github.com/SINTEF/soft7/issues/9)
- github actions for pypi publishing [\#3](https://github.com/SINTEF/soft7/issues/3)
- github actions for unittesting [\#2](https://github.com/SINTEF/soft7/issues/2)
- Add dependabot and pre-commit.ci configurations [\#23](https://github.com/SINTEF/soft7/pull/23) ([CasperWA](https://github.com/CasperWA))

**Closed issues:**

- Disable autofixing PRs via pre-commit.ci [\#37](https://github.com/SINTEF/soft7/issues/37)
- New docs build is failing [\#34](https://github.com/SINTEF/soft7/issues/34)
- Use ruff instead of pylint [\#18](https://github.com/SINTEF/soft7/issues/18)
- Consider `def` functions instead of lambda [\#15](https://github.com/SINTEF/soft7/issues/15)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#39](https://github.com/SINTEF/soft7/pull/39) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Consolidate `develop` [\#38](https://github.com/SINTEF/soft7/pull/38) ([CasperWA](https://github.com/CasperWA))
- Data Source factory upgrade \(`develop` edition\) [\#36](https://github.com/SINTEF/soft7/pull/36) ([CasperWA](https://github.com/CasperWA))
- Fix documentation workflow [\#35](https://github.com/SINTEF/soft7/pull/35) ([CasperWA](https://github.com/CasperWA))
- Added s7.graph module which includes functions to fetch subgraphs [\#33](https://github.com/SINTEF/soft7/pull/33) ([quaat](https://github.com/quaat))
- \[pre-commit.ci\] pre-commit autoupdate [\#32](https://github.com/SINTEF/soft7/pull/32) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#30](https://github.com/SINTEF/soft7/pull/30) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#29](https://github.com/SINTEF/soft7/pull/29) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#28](https://github.com/SINTEF/soft7/pull/28) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#26](https://github.com/SINTEF/soft7/pull/26) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Documentation [\#25](https://github.com/SINTEF/soft7/pull/25) ([CasperWA](https://github.com/CasperWA))
- Update pytest-cov requirement from ~=4.1 to \>=4.1,\<6.0 [\#24](https://github.com/SINTEF/soft7/pull/24) ([dependabot[bot]](https://github.com/apps/dependabot))
- Run CI tests for pushes to 'develop' [\#22](https://github.com/SINTEF/soft7/pull/22) ([CasperWA](https://github.com/CasperWA))
- Entity factory and cleanup [\#21](https://github.com/SINTEF/soft7/pull/21) ([CasperWA](https://github.com/CasperWA))
- Use ruff [\#19](https://github.com/SINTEF/soft7/pull/19) ([CasperWA](https://github.com/CasperWA))
- Update to pydantic v2 [\#16](https://github.com/SINTEF/soft7/pull/16) ([CasperWA](https://github.com/CasperWA))
- Update pre-commit hooks [\#14](https://github.com/SINTEF/soft7/pull/14) ([CasperWA](https://github.com/CasperWA))
- Publish workflow [\#13](https://github.com/SINTEF/soft7/pull/13) ([CasperWA](https://github.com/CasperWA))
- Add dev tools \(pre-commit with several hooks\) [\#10](https://github.com/SINTEF/soft7/pull/10) ([CasperWA](https://github.com/CasperWA))



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
