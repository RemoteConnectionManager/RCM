# Next Release
## General

* [dev :computer:]: Adopted *git-flow*/*pull-request* flow.
* [dev :computer:]: Renamed main branches to *git-flow* standard.
* [dev :computer:]: Clean up branches.
* [dev :computer:]: Add `CHANGELOG.md` and `CONTRIBUTION.md`.

## Client

* [ci :robot:]: Build RCM client workflow to create artifacts on *Ubuntu*, *Windows* and *macOS*.
* [ci :robot:]: Add workaround to download artifacts without logging in.
* [dev :computer:]: Add scripts to setup build environment on different OS.
* [dep :herb:]: Update *Python* version to `3.10.11`.
* [dep :herb:]: Update *Python* dependencies.
* [dep :herb:]: Update *paramiko* to `3.4` (patch required to work with *step*).
* [dep :herb:]: Update *TurboVNC* to `3.x` (Windows executable is changed, patch to *Java* required to work with old RCM servers).
* [dep :herb:]: Add *step* executables in the bundle.
* [bug :beetle:]: Fix `subprocess` call on windows (pop up *cmd* terminal).
* [gui :window:]: Add **RCM** logo in the GUI.
* [release :package:]: Add *cosign* signature.