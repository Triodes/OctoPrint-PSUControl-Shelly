---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: Triodes

---

### Describe the bug
A clear and concise description of what the bug is.

### To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

### Expected behavior
A clear and concise description of what you expected to happen.

### Screenshots
If applicable, add screenshots to help explain your problem. Also, please include screenshots of the config pages of both PSUControl and PSU Control - Shelly.

### Logs
Please set Logging for *octoprint.plugins.psucontrol_shelly* to **DEBUG** and attach *octoprint.log* to your report.

### Just to be sure
* Did you double check that the *PSU Control - Shelly* plugin is selected for ***Sensing as well as Switching*** in the PSU Control settings? Misconfiguration of this setting has been the cause of most of the reported issues.
* Did you disable Auto-On in the PSU Control settings? This _will_ cause erratic behaviour in the plugin and is not considered a bug since it cannot be resolved.

### To be very sure
Did you read the previous paragraph and check the settings? From now on, these misconfigurations will be closed without further explanation.
