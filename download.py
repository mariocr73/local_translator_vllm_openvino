from huggingface_hub import snapshot_download
import os

repo = os.environ.get("MODEL_ID")
if not repo:
    raise SystemExit("MODEL_ID env var is required")

local = f"/models/{repo}"
os.makedirs(local, exist_ok=True)

print(f"Downloading {repo} to {local}")
snapshot_download(
    repo_id=repo,
    local_dir=local,  # se recomienda no usar local_dir_use_symlinks
    token=os.environ.get("HUGGINGFACE_HUB_TOKEN") or None,
)
print("OK")

