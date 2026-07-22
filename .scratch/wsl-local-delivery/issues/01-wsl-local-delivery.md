# 01 - WSL local delivery

Type: feature
Status: resolved
Labels: ready-for-agent

- [x] Provide install, deploy, start/stop/status/logs, and health commands.
- [x] Verify build and HTTP health checks before reporting deployment success.

## Answer

The WSL deployment is now managed by `trading-toolkit.service`; the versioned operator script installed it, completed a production build, and verified Web and service reachability.
