[comment]: # ( https://github.com/nayafia/contributing-template/blob/master/CONTRIBUTING-template.md )

[comment]: # ( https://github.com/cookiecutter/cookiecutter/blob/main/CONTRIBUTING.md#types-of-contributions )

# Contributing
This document explains how you can contribute on RCM development.

## Type of contributions
You can contribute in may ways:

### Report Bugs 
You can open a new issue here: https://github.com/RemoteConnectionManager/RCM/issues

Please, include:

* Your operating system name and version.
* Your RCM version or your local development environment.
* If you can, provide detailed steps to reproduce the bug.
* If you don't have steps to reproduce the bug, just note your observations in as much detail as you can. Questions to start a discussion about the issue are welcome.

### Fix Bugs or Implement Features
Look through the GitHub issues for bugs.

Please do not combine multiple feature enhancements into a single pull request.


### Write Documentation
Add documentation on development processes, add docstring to the code or help us to write a user guide.

## Setting Up Local Development

1. Fork `RCM` repo on GitHub (https://github.com/RemoteConnectionManager/RCM/fork).

1. Clone your fork locally:
   ```shell
   $ git clone git@github.com:<your_name_here>/RCM.git
   ```

1. Based on your platform, install the proper version of *Python*, configure the *Python* virtual environment and download and extract external packages. You can check the steps from `RCM/.github/workflows/main.yaml` or use the installation scripts in the `RCM/` folder.
   ```shell 
   # Ubuntu setup
   # Install missing Qt lWibraries
   $ sudo apt update
   $ sudo apt install qtbase5-dev qt5-qmake qtwayland5
   $ RCM/scripts/ci/setup.sh
   ```
   ```shell
   # macOS setup
   $ RCM/scripts/ci/setup.sh
   ```
   ```PowerShell
   # Windows setup
   > RCM\scripts\ci\setup.ps1
   ```

1. Start using `git-flow` by initializing your git repository:
   ```shell
   $ cd ./RCM
   $ git flow init --defaults
   ```

1. Start a new feature based on your contribution:
   ```shell
   $ git flow feature start <your_feature_name>
   ```

1. Publish your feature with command:
   ```shell
   $ git flow feature publish <your_feature_name>
   ```
   This is useful if you are developing a feature in collaboration :handshake:, if you want to run GitHub workflow :robot:. 

1. Contribute :heart:!
   You can commit your change with commands:
   ```shell
   $ git commit -a -m "category: My amazing changes"
   $ git push
   ```

1. Submit a pull request through the GitHub website, and wait for the approval :crossed_fingers:.

1. [Optional :broom:] Once your request has been accepted, you can delete your feature with the command:
   ```shell
   $ git flow feature delete --remote --force <your_feature_name>
   ```
   and/or delete your forked repository from GitHub website.


## Contributor Guidelines
### Pull Request Guidelines
Before you submit a pull request, check that it meets these guidelines:

1. The pull request should be contained: if it's too big consider splitting it into smaller pull requests.

1. Update the `CHANGELOG.md`, by adding a description of your feature or bug fix.

1. The pull request must pass all CI/CD jobs before being ready for review.

[comment]: # ( 1. If one CI/CD job is failing for unrelated reasons you may want to create another PR to fix that first. )


[comment]: # ( ### Coding Standards )
