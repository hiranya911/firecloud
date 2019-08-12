# Taprobana

## Introduction

Taprobana is a release notes generation tool for GitHub repositories. Simply add a `release-note`
label to your pull requests on GitHub to indicate that they should be included in the relase
notes, and execute Taprobana as shown below:

```
$ python taprobana.py OrgName/RepoName
```

This will go through the pull requests in the https://github.com/OrgName/RepoName repo to
identify the changes merged since the last release. Then it will extract release notes from the
pull requests labelled with `release-note`, and present the output in markdown format.

## Requirements

* Python 2.7 or 3.x
* The `requests` library

## Features

1. Automatic pull request discovery:
    * Auto discovers the last release pull request by scanning for a specific title prefix
      (e.g. `Bumped version to`). Title prefix configurable via the `--title-prefix` option.
    * Alternatively, specify the last release pull request number with the `--since-pr`
      option.
    * Supports configuring the base branch to scan for pull requests via the `--branch` option.
    * Can also scan across all branches by setting the `--branch` option to `*`.
    * Extend the discovery mechanism further by implementing the `github.PullRequestSearchStrategy`
      interface.

1. Release note extraction:
    * Extracts release notes from pull requests carrying the label `release-note`.
    * Supports conventional commits format. If the pull request title is in the conventional
      commits format, determines the type (e.g. feature, fix) and the scope (e.g. auth, fcm) of
      the release notes from the title.
    * If the pull request title is not in the conventional format, uses the title as a release
      note, with the type set to "fix".
    * Allows explicitly specifying release notes in the pull request description.
      Any line with the prefix `RELEASE NOTE:` is considered a release note. Any markdown in the
      text will appear as is in the generated output.
    * Allows documenting API changes in the pull request description with the prefix
      `API CHANGE:`.

1. Release note generation:
    * Generates markdown content for both the Firebase Devsite and GitHub releases page.
    * Uses relative URLs and other known text placeholders in the release notes generated for the
      Devsite. Wraps the output to 80 columns for easier inclusion in google3.
    * Uses absolute URLs and unwrapped output for GitHub output.
    * If a pull request is a contribution from an external developer, automatically includes a
      "thank you note" in the generated output.
    * Support specifying the next release version number via the `--next-version` option. If not
      specified, estimates the next version based on the release notes.
    * Supports specifyign the release date via the `--date` option. If not specified, sets the
      release date to the following day.
    * Extend the output generation or support other output formats by implementing the
      `formatters.ReleaseNoteFormatter` interface.
