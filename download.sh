#!/usr/bin/env bash
# Create required directories
mkdir -p .storyline resource

# 1. Download models.zip to .storyline/ and extract it (keep original directory name)
wget "https://image-url-2-feature-1251524319.cos.ap-shanghai.myqcloud.com/openstoryline/models.zip" \
  -O .storyline/models.zip

unzip -o .storyline/models.zip -d .storyline/models/

# Remove the original archive
rm .storyline/models.zip


# 2. Download resource.zip to .storyline/ and extract it into ./resource
wget "https://image-url-2-feature-1251524319.cos.ap-shanghai.myqcloud.com/openstoryline/resource.zip" \
  -O .storyline/resource.zip

unzip -o .storyline/resource.zip -d resource

# Remove the original archive
rm .storyline/resource.zip

# List of filenames
files=("brand_black.png" "brand_white.png" "logo.png" "dice.png" "github.png" "node_map.png" "user_guide.png")

# Base URL
base_url="https://image-url-2-feature-1251524319.cos.ap-shanghai.myqcloud.com/zailin/datasets/open_storyline"

# Download each file
for f in "${files[@]}"; do
    wget "$base_url/$f" -O "web/static/$f"
done