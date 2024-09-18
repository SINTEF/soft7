# Changelog

## [Unreleased](https://github.com/SINTEF/soft7/tree/HEAD)

[Full Changelog](https://github.com/SINTEF/soft7/compare/v0.2.1...HEAD)

## Remove upper limit for `oteapi-core` dependency

While not recommended, this does make it possible to support the DataSpaces developed at SINTEF.
In the future a more stringent dependency tree/graph should be implemented for all packages.

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
