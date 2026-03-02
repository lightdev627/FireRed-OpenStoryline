if git show-ref --verify --quiet refs/heads/hf-clean; then
    git branch -D hf-clean
    echo "Deleted existing hf-clean branch"
else
    echo "hf-clean branch does not exist"
fi
git checkout --orphan hf-clean
git reset
git add .
GIT_COMMITTER_NAME="minipuding" GIT_COMMITTER_EMAIL="minipuding@users.noreply.github.com" \
git commit -m "Clean branch for Open-Storyline push" \
    --author="minipuding <minipuding@users.noreply.github.com>"
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_xusijie -v" git push github hf-clean:main --force
git checkout release/v1.0.0202