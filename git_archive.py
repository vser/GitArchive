#!/usr/bin/env python3
import argparse
from pathlib import Path
import subprocess
import sys
import time
from typing import List, Optional
import zipfile

# ==============================================================================
# USER CONFIGURATION & SETTINGS
# Edit the variables below to customize default behavior without CLI flags.
# ==============================================================================

# Directory where repositories and commit archives will be saved.
# Default: ~/GitArchive (a folder named "GitArchive" in your user home directory)
ARCHIVE_ROOT = Path.home() / "GitArchive"

# File containing the list of Git repositories to sync (one URL per line).
# Default: "repo_list.txt" located in the same folder as this script.
DEFAULT_REPO_LIST = Path(__file__).parent / "repo_list.txt"

# Maximum number of most recent commits to archive per repository:
# - Set to a number (e.g. 50) to archive only the latest 50 commits and
#   automatically delete (prune) older ZIPs that fall outside this window.
# - Set to None to archive every commit across the entire repository history.
RECENT_ARCHIVE_LIMIT = None

# Default repeat interval for monitoring repositories (in minutes):
# - Set to an integer (e.g. 30) to continuously check for updates every 30 mins.
# - Set to None to run once and exit immediately.
DEFAULT_WATCH_MINUTES = None

# ==============================================================================
# END OF USER CONFIGURATION
# ==============================================================================


def run_cmd(cmd, cwd=None):
    """Run a shell command and return stdout."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def load_repositories(list_path: Path) -> List[str]:
    """Read repository URLs from a text file (ignores blank lines/comments)."""
    if not list_path.exists():
        print(f"[!] Repo list not found: {list_path}", file=sys.stderr)
        return []

    repos = []
    for line in list_path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("#"):
            repos.append(cleaned)
    return repos


def archive_commit(commit_hash: str, mirror_dir: Path, target_zip: Path):
    """Archive a commit's tree into a ZIP and embed commit_info.txt."""
    temp_zip = target_zip.with_suffix(".tmp.zip")

    try:
        # 1. Create base ZIP archive directly using Git
        run_cmd(
            [
                "git",
                "archive",
                "--format=zip",
                "-o",
                str(temp_zip),
                commit_hash,
            ],
            cwd=mirror_dir,
        )

        # 2. Retrieve commit metadata and append to the ZIP
        info = run_cmd(
            ["git", "log", "-1", "--stat", commit_hash], cwd=mirror_dir
        )
        with zipfile.ZipFile(temp_zip, mode="a") as zf:
            zf.writestr("commit_info.txt", info)

        # 3. Atomically rename to final target path
        temp_zip.replace(target_zip)
    finally:
        if temp_zip.exists():
            temp_zip.unlink(missing_ok=True)


def sync_repository(
    repo_url: str, recent_archive_limit: Optional[int] = None
):
    clean_name = repo_url.rstrip("/").split("/")[-1]
    if clean_name.endswith(".git"):
        clean_name = clean_name[:-4]

    repo_root = ARCHIVE_ROOT / clean_name
    mirror_dir = repo_root / f"{clean_name}.git"
    commits_dir = repo_root / "commits"

    repo_root.mkdir(parents=True, exist_ok=True)
    commits_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 15} Processing {clean_name} {'=' * 15}")

    # 1. Update or create the Git mirror
    if not mirror_dir.exists():
        print("[*] Cloning full bare mirror...")
        run_cmd(["git", "clone", "--mirror", repo_url, str(mirror_dir)])
    else:
        print("[*] Updating mirror from remote...")
        run_cmd(["git", "remote", "update"], cwd=mirror_dir)

    # 2. Get list of all commits with commit date (YYYY-MM-DD)
    commits_raw = run_cmd(
        [
            "git",
            "log",
            "--all",
            "--date-order",
            "--reverse",
            "--format=%H %cs",
        ],
        cwd=mirror_dir,
    )

    commits = []
    for line in commits_raw.splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            commits.append((parts[0], parts[1]))

    total_commits = len(commits)
    print(f"[*] Found {total_commits} total commit(s) in history.")

    # Apply limit to keep only the latest N commits
    if recent_archive_limit is not None and recent_archive_limit > 0:
        commits = commits[-recent_archive_limit:]
        print(f"[*] Retaining the {len(commits)} most recent commit(s).")

    # 3. Archive commits to dated ZIP files
    skipped = 0
    archived = 0
    total = len(commits)

    for idx, (commit_hash, commit_date) in enumerate(commits, 1):
        zip_filename = f"{commit_date}_{commit_hash}.zip"
        target_zip = commits_dir / zip_filename

        if target_zip.exists() and target_zip.stat().st_size > 0:
            skipped += 1
            continue

        short_hash = commit_hash[:8]
        print(f"[{idx}/{total}] Zipping {commit_date}_{short_hash}...")
        archive_commit(commit_hash, mirror_dir, target_zip)
        archived += 1

    # 4. Prune older ZIP archives exceeding the retention limit
    pruned = 0
    if recent_archive_limit is not None and recent_archive_limit > 0:
        active_zips = {
            f"{c_date}_{c_hash}.zip" for c_hash, c_date in commits
        }
        for existing_zip in commits_dir.glob("*.zip"):
            if existing_zip.name.endswith(".tmp.zip"):
                continue
            if existing_zip.name not in active_zips:
                existing_zip.unlink(missing_ok=True)
                pruned += 1

    summary = f"[✓] Complete. New: {archived} | Skipped: {skipped} cached"
    if pruned > 0:
        summary += f" | Pruned: {pruned} old"
    print(summary)
    print(f"[✓] Path: {repo_root.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="GitArchive: Bare Git mirror and commit-level ZIP archiver."
    )
    parser.add_argument(
        "--repos",
        type=Path,
        default=DEFAULT_REPO_LIST,
        help="Path to file containing git repository URLs (default: repo_list.txt).",
    )
    parser.add_argument(
        "--recent-archive-limit",
        type=int,
        default=RECENT_ARCHIVE_LIMIT,
        metavar="N",
        help="Number of most recent commits to keep (archives new, prunes older).",
    )
    parser.add_argument(
        "--watch",
        type=int,
        default=DEFAULT_WATCH_MINUTES,
        metavar="MINUTES",
        help="Continuously monitor and check for updates every X minutes.",
    )
    args = parser.parse_args()

    if (
        args.recent_archive_limit is not None
        and args.recent_archive_limit <= 0
    ):
        parser.error("--recent-archive-limit must be a positive integer.")

    if args.watch is not None and args.watch <= 0:
        parser.error("--watch must be a positive integer.")

    while True:
        repositories = load_repositories(args.repos)
        if not repositories:
            print("[!] No repositories found to sync. Exiting.")
            sys.exit(1)

        for repo_url in repositories:
            try:
                sync_repository(
                    repo_url,
                    recent_archive_limit=args.recent_archive_limit,
                )
            except Exception as err:
                print(f"[!] Error syncing {repo_url}: {err}", file=sys.stderr)

        if not args.watch:
            break

        print(
            f"\nSleeping for {args.watch} minute(s)... (Press Ctrl+C to exit)"
        )
        try:
            time.sleep(args.watch * 60)
        except KeyboardInterrupt:
            print("\nStopped.")
            break


if __name__ == "__main__":
    main()
