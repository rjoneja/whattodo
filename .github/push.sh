#!/usr/bin/env bash
# Commit this workflow's outputs and push them, even when main moved on meanwhile.
#   .github/push.sh "content 2026-11-05" docs/events.json venues.json ...
# On a clash, JSON files are merged entry by entry (.github/merge_json.py): both sides' changes are kept, and
# where both touched the same field the workflow's fresh value wins. Other files (generated pages) take this
# workflow's version. Nothing is ever lost silently: if all retries fail the step fails.
set -u
msg=$1; shift
git config user.name bot && git config user.email bot@users.noreply.github.com
for f in "$@"; do [ -e "$f" ] && git add -- "$f"; done
git diff --cached --quiet && { echo "nothing to commit"; exit 0; }
git commit -qm "$msg"
for i in 1 2 3 4 5 6; do
  git fetch -q origin main
  if git rebase -q origin/main 2>/dev/null; then
    git push -q origin HEAD:main && { echo "pushed"; exit 0; }
  else
    for f in $(git diff --name-only --diff-filter=U); do
      case "$f" in
        *.json) python3 .github/merge_json.py "$f" || git checkout --theirs -- "$f" 2>/dev/null ;;
        *)      git checkout --theirs -- "$f" 2>/dev/null ;;   # during a rebase, "theirs" is this workflow's commit
      esac
      if [ -e "$f" ]; then git add -- "$f"; else git rm -q --cached -- "$f" 2>/dev/null; fi
    done
    if GIT_EDITOR=true git rebase --continue >/dev/null 2>&1; then
      git push -q origin HEAD:main && { echo "pushed (merged with main)"; exit 0; }
    else
      git rebase --abort 2>/dev/null
    fi
  fi
  echo "push failed, retry $i"; sleep $((i*10))
done
echo "push never succeeded"; exit 1
