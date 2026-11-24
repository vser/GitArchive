# GitArchive

A lightweight tool that mirrors Git repositories and exports each commit into an independent, dated snapshot `.zip` file containing an embedded `commit_info.txt` metadata log.

## Features

- **Bare Mirrors:** Clones and keeps full bare Git mirrors synchronized.
- **Commit Snapshots:** Exports individual commits directly to standalone `.zip` archives.
- **Commit Retention:** Optional `--recent-archive-limit` to store only the latest $N$ commits and automatically prune older archives.
- **Watch Mode:** Continuously syncs on a scheduled interval.
- **Zero External Dependencies:** Built entirely with the Python standard library.
- **Simple Configuration:** Plaintext URL list (`repo_list.txt`).

## Supported Git Hosts

Because GitArchive relies on native `git` commands, it works with any Git provider or server accessible over HTTPS or SSH:

- **GitHub** (`github.com`)
- **GitLab** (`gitlab.com` & self-hosted instances)
- **Codeberg** (`codeberg.org`)
- **Bitbucket** (`bitbucket.org`)
- **SourceHut** (`sr.ht`)
- **Gitea / Forgejo** instances
- **Self-hosted / Private Git servers** (cgit, Gitolite, bare remote servers)

## Requirements

- **Python 3.8+** (Uses standard library only—no `pip install` required)
- **Git CLI**

### SteamOS / Steam Deck Setup

Python 3 and Git are often available out of the box or can be set up in Desktop Mode:

1. Switch to **Desktop Mode** (Steam Menu > Power > Switch to Desktop).
2. Open **Konsole** and verify existing installations:
   ```bash
   python3 --version
   git --version
   ```
3. If either is missing, install them via `pacman` (requires setting an admin password via `passwd` first if you haven't already):
   ```bash
   sudo steamos-readonly disable
   sudo pacman-key --init
   sudo pacman-key --populate archlinux holo
   sudo pacman -Sy --needed python git
   sudo steamos-readonly enable
   ```

## Quick Start

1. Add target Git URLs to `repo_list.txt` (one per line):
   ```text
   https://github.com/user/repo-name.git
   https://gitlab.com/user/another-repo.git
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
