# Next Release
## General

* :computer:`[dev]`: Adopted *git-flow*/*pull-request* flow.
* :books:`[doc]`: Add `CHANGELOG.md` and `CONTRIBUTION.md`.

[comment]: <> (* :computer:`[dev]`: Renamed main branches to *git-flow* standard.)
[comment]: <> (* :computer:`[dev]`: Clean up branches.)

## Client

* :robot:`[ci]`: Build RCM client workflow to create artifacts on *Ubuntu*, *Windows* and *macOS*.
* :robot:`[ci]`: Add workaround to download artifacts without logging in.
* :computer:`[dev]`: Add scripts to setup build environment on different OS.
* :herb:`[dep]`: Update *Python* version to `3.10.11`.
* :herb:`[dep]`: Update *Python* dependencies.
* :herb:`[dep]`: Update *paramiko* to `3.4` (patch required to work with *step*).
* :herb:`[dep]`: Update *TurboVNC* to `3.x` (Windows executable is changed, patch to *Java* required to work with old RCM servers).
* :herb:`[dep]`: Add *step* executables in the bundle.
* :beetle:`[bug]`: Fix `subprocess` call on windows (pop up *cmd* terminal).
* :window:`[gui]`: Add **RCM** logo in the GUI.
* :package:`[release]`: Add *cosign* signature.