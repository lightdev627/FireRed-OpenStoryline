import os
import sys
import argparse
import base64
import hashlib
import json
from openai import OpenAI
from src.open_storyline.utils.prompts import get_prompt
from src.open_storyline.utils.parse_json import parse_json_dict
from tqdm import tqdm  # progress bar

# -------------------------------
# Get API key from environment
# -------------------------------
API_KEY = os.environ.get("QWEN_API_KEY", "")

client = None
if API_KEY:
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

# -------------------------------
# Utility functions
# -------------------------------
def file_md5(path: str) -> str:
    """Compute MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def process_bgm(path: str, prompt_text: str) -> dict:
    """Call Qwen3-Omni to generate JSON labels for a single audio file."""
    if not client:
        raise RuntimeError("API client not initialized")  # safety check

    with open(path, "rb") as f:
        audio_bytes = f.read()
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    completion = client.chat.completions.create(
        model="qwen3-omni-flash-2025-12-01",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": f"data:audio/wav;base64,{audio_b64}",
                            "format": "wav"
                        }
                    },
                    {"type": "text", "text": prompt_text}
                ],
            }
        ],
        modalities=["text"],
        stream=True,
        stream_options={"include_usage": True},
    )

    # Concatenate streaming text
    texts = []
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            texts.append(chunk.choices[0].delta.content)
    res = parse_json_dict("".join(texts))
    return res

# -------------------------------
# Main batch processing
# -------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir", type=str, default="resource/bgms", help="BGM folder path"
    )
    parser.add_argument(
        "--output_json", type=str, default="resource/bgms/meta.json", help="Output JSON file"
    )
    args = parser.parse_args()

    input_dir = args.input_dir
    output_json = args.output_json

    # Load existing meta.json if exists
    if os.path.exists(output_json):
        with open(output_json, "r", encoding="utf-8") as f:
            meta_data = json.load(f)
    else:
        meta_data = []

    # Map MD5 -> dict for quick lookup
    md5_map = {item["id"]: item for item in meta_data}

    # Get prompt
    prompt_text = get_prompt("scripts.omni_bgm_label", lang="zh")

    # Scan audio files
    files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith((".mp3", ".wav"))
    ]

    updated_meta = []
    needs_processing = False  # Flag to track if there are new/changed files

    # Iterate with progress bar
    for file_path in tqdm(files, desc="Processing BGMs", unit="file"):
        # Make path relative to 'resource/' folder
        resource_root = os.path.join(os.path.dirname(output_json), "../../..")
        rel_path = os.path.relpath(file_path, start=resource_root).replace("\\", "/")
        md5 = file_md5(file_path)

        # Skip unchanged files
        if md5 in md5_map:
            updated_meta.append(md5_map[md5])
            continue

        # Mark that we have new/changed file
        needs_processing = True

        # Display current file in progress bar
        tqdm.write(f"Processing {rel_path} ...")

        # If no API key, warn once and skip processing
        if not client:
            continue  # skip actual labeling, warning printed later

        # Try to process BGM safely
        try:
            res = process_bgm(file_path, prompt_text)
        except Exception as e:
            tqdm.write(f"⚠️ Error processing {rel_path}: {e}")
            continue

        # Add path and id
        res["path"] = rel_path
        res["id"] = md5
        updated_meta.append(res)

    # Print warning if needed
    if not client and needs_processing:
        print(
            "⚠️ Warning: OpenAI API key is empty. Omni model not available, cannot label new or changed BGM files."
        )

    # Save meta.json
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(updated_meta, f, ensure_ascii=False, indent=2)

    print(f"✅ Done! meta.json saved to {output_json}")


if __name__ == "__main__":
    main()