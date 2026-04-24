# Git Remotes

| Remote | URL | Purpose |
|--------|-----|---------|
| origin | https://github.com/TanSento/Agent_Track.git | Personal repo — push work here |
| upstream | https://github.com/ed-donner/agents.git | Course repo — pull updates from here |

## Common commands

Pull latest course updates:
```bash
git fetch upstream
git merge upstream/main
```

Push your work:
```bash
git push origin main
```

Restore a folder from the course repo:
```bash
git checkout upstream/main -- <path/to/folder>
```
