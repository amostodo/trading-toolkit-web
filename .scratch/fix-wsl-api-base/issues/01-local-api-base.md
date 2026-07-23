# 01 - Local API Base

Type: bug
Status: resolved
Labels: bug, deployment

Build the WSL preview with the local Flask API base and verify the convertible placement list loads.

## Answer

The WSL-managed Vite server now proxies same-origin `/api` requests to the local Flask service. On 2026-07-23, the persisted pending endpoint returned two candidates and the refreshed Web page rendered `配售 2` with 炬申股份 and 申能股份.
