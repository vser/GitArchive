# GitArchive

A lightweight tool that mirrors Git repositories and exports each commit into an independent, dated snapshot `.zip` file containing an embedded `commit_info.txt` metadata log.

## Features

- **Bare Mirrors:** Clones and keeps full bare Git mirrors synchronized.
- **Commit Snapshots:** Exports individual commits directly to standalone `.zip` archives.
- **Commit Retention:** Optional `--recent-archive-limit` to store only the latest $N$ commits and automatically prune older archives.
- **Watch Mode:** Continuously syncs on a scheduled interval.
- **Simple Configuration:** Plaintext URL list (`repo_list.txt`).

## Quick Start

1. Add target Git URLs to `repo_list.txt` (one per line):
   ```text
   https://github.com/user/repo-name.git
   ```

2. Run the archiver:
   ```bash
   python3 git_archive.py
   ```

Archives are saved to `~/GitArchive/<repo_name>/`.

## Options

- **Keep only the latest 50 commits:**
  ```bash
  python3 git_archive.py --recent-archive-limit 50
  ```

- **Run continuously every 30 minutes:**
  ```bash
  python3 git_archive.py --watch 30
  ```

- **Use a custom repository list:**
  ```bash
  python3 git_archive.py --repos my_repos.txt
  ```

---

## AI Disclaimer

This project was developed and refactored with the assistance of artificial intelligence (AI). Please review and test the script to ensure it meets your specific environment and safety requirements.
