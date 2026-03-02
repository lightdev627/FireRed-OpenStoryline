# Please install OpenAI SDK first: `pip install openai`
import os
import argparse
import hashlib
import json
from openai import OpenAI
from tqdm import tqdm

from src.open_storyline.utils.prompts import get_prompt
from src.open_storyline.utils.parse_json import parse_json_dict

# -------------------------------
# API client (DeepSeek / OpenAI compatible)
# -------------------------------
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

client = None
if API_KEY:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.deepseek.com/v1",
    )

# -------------------------------
# Utils
# -------------------------------
def file_md5(path: str) -> str:
    """Compute MD5 of file content."""
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5.hexdigest()


def label_template(path: str, system_prompt: str) -> dict:
    """Call LLM to label a single text template."""
    if not client:
        raise RuntimeError("API client not initialized")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        stream=False,
    )

    return parse_json_dict(resp.choices[0].message.content)


# -------------------------------
# Main
# -------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir",
        type=str,
        default="resource/script_templates",
        help="Folder containing .txt style templates",
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default="resource/script_templates/meta.json",
        help="Output meta.json path",
    )
    args = parser.parse_args()

    input_dir = args.input_dir
    output_json = args.output_json

    # Load existing meta.json (resume support)
    if os.path.exists(output_json):
        with open(output_json, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
    else:
        meta_data = []

    # md5 -> item
    md5_map = {item["id"]: item for item in meta_data}

    # Prompt
    system_prompt = get_prompt("scripts.script_template_label", lang="zh")

    # Collect txt files
    files = []
    for root, _, filenames in os.walk(input_dir):
        for name in filenames:
            if name.lower().endswith(".txt"):
                files.append(os.path.join(root, name))

    updated_meta = []
    needs_processing = False

    # resource 根目录（用于算相对路径）
    resource_root = os.path.abspath(os.path.join(input_dir, "../.."))

    for file_path in tqdm(files, desc="Labeling templates", unit="file"):
        md5 = file_md5(file_path)

        rel_path = os.path.relpath(file_path, start=resource_root).replace("\\", "/")

        # 未变化，直接复用
        if md5 in md5_map:
            updated_meta.append(md5_map[md5])
            continue

        needs_processing = True
        tqdm.write(f"Processing {rel_path} ...")

        if not client:
            continue

        try:
            res = label_template(file_path, system_prompt)
        except Exception as e:
            tqdm.write(f"⚠️ Failed on {rel_path}: {e}")
            continue

        # 补充字段
        res["id"] = md5
        res["path"] = rel_path

        updated_meta.append(res)

    if not client and needs_processing:
        print("⚠️ Warning: API key missing, new/changed templates were not labeled.")

    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(updated_meta, f, ensure_ascii=False, indent=2)

    print(f"✅ Done! meta.json saved to {output_json}")


if __name__ == "__main__":
    main()