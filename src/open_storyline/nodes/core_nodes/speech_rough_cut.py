from typing import Any, Dict
from pathlib import Path

from open_storyline.nodes.core_nodes.base_node import BaseNode, NodeMeta
from open_storyline.nodes.node_state import NodeState
from open_storyline.nodes.node_schema import SpeechRoughCutInput
from open_storyline.utils.prompts import get_prompt
from open_storyline.utils.parse_json import parse_json_list
from open_storyline.utils.ffmpeg_utils import (
    resolve_ffmpeg_executable,
    read_video_frames_as_rgb24,
    segment_video_stream_copy_with_ffmpeg,
    VideoSegment,
)
from open_storyline.utils.register import NODE_REGISTRY

CLIP_ID_NUMBER_WIDTH = 4
MILLISECONDS_PER_SECOND = 1000.0

@NODE_REGISTRY.register()
class SpeechRoughCutNode(BaseNode):

    meta = NodeMeta(
        name="speech_rough_cut",
        description="Perform rough cut on speech clips based on ASR results",
        node_id="speech_rough_cut",
        node_kind="speech_rough_cut",
        require_prior_kind=['asr'],
        default_require_prior_kind=['asr'],
        next_available_node=[],
    )

    input_schema = SpeechRoughCutInput

    def __init__(self, server_cfg):
        super().__init__(server_cfg)
        self.ffmpeg_executable = resolve_ffmpeg_executable()

    async def default_process(
        self,
        node_state,
        inputs: Dict[str, Any],
    ) -> Any:
        return {}

    async def process(self, node_state: NodeState, inputs: Dict[str, Any]) -> Any:
        
        asr_infos = inputs["asr"].get('asr_infos', [])
        gap_threshold = inputs.get('gap_threshold', 400)
        output_directory = self._prepare_output_directory(node_state, inputs)
        llm = node_state.llm
        rough_cut_jsons, clips, clip_index = [], [], 0

        system_prompt = get_prompt("speech_rough_cut.system", lang=node_state.lang)

        for asr_info in asr_infos:
            
            video_path = asr_info.get('path')
            source_ref = asr_info.get('source_ref', {})
            fps = asr_info.get('fps', 30)
            user_prompt = get_prompt(
                "speech_rough_cut.user",
                lang=node_state.lang,
                asr_sentence_info=asr_info.get("asr_sentence_info", {})
            )

            # If there is no audio, or ASR failed, skip rough cut and keep the original clip
            try:
                raw = await llm.complete(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    media=None,
                    temperature=0.1,
                    top_p=0.9,
                    max_tokens=8092,
                    model_preferences=None,
                )
            except Exception as e:
                last_error = e

            # If LLM fails to generate rough cut JSON, skip rough cut and keep the original clip
            try:
                rough_cut_json = parse_json_list(raw)
                segments = self.group_sentences(rough_cut_json, gap_threshold=gap_threshold)
                ranges = self.segments_to_ranges(segments)
                cuts = self.ranges_to_cut_points(ranges)
                split_points_seconds = [t/1000 for t in cuts]
                segments = segment_video_stream_copy_with_ffmpeg(
                    input_video=video_path,
                    ffmpeg_executable=self.ffmpeg_executable,
                    split_points_seconds=split_points_seconds,
                    output_directory=output_directory,
                    filename_prefix=f"speech_rough_cut_{clip_index:0{CLIP_ID_NUMBER_WIDTH}d}",
                    start_index=len(rough_cut_jsons),
                )
                rough_cut_jsons.append(rough_cut_json)
            except Exception as e:
                last_error = e
        
            # Filter segments to keep only the first segment of each pair (i.e., segments[0], segments[2], etc.)
            filtered_segments = [seg for i, seg in enumerate(segments) if i % 2 == 0]

            for segment in filtered_segments:
                clip_id = self._format_clip_id(clip_index)

                start_milliseconds = max(0, int(round(segment.start_seconds * MILLISECONDS_PER_SECOND)))
                end_milliseconds = max(start_milliseconds, int(round(segment.end_seconds * MILLISECONDS_PER_SECOND)))

                segment_duration_milliseconds = max(0, end_milliseconds - start_milliseconds)
                if segment_duration_milliseconds <= 0:
                    continue

                output_path_string = str(segment.path)
                node_state.node_summary.info_for_user(f"{clip_id} split successfully", preview_urls=[output_path_string])

                clips.append(
                    {
                        "clip_id": clip_id,
                        "kind": "video",
                        "path": output_path_string,
                        "fps": fps,
                        "source_ref": {
                            "media_id": source_ref.get("media_id"),
                            "start": start_milliseconds,
                            "end": end_milliseconds,
                            "duration": segment_duration_milliseconds,
                            "height": source_ref.get("height"),
                            "width": source_ref.get("width"),
                        },
                    }
                )
                clip_index += 1
        
        return {"clips": clips, "rough_cut_jsons": rough_cut_jsons}
    

    def group_sentences(self, items, gap_threshold: int=400):
        segments = []
        current = [items[0]]

        for i in range(len(items) - 1):
            cur = items[i]
            next = items[i+1]

            gap = next["start"] - cur["end"]

            if gap > gap_threshold:
                segments.append(current)
                current = [next]
            else:
                current.append(next)

        if current:
            segments.append(current)

        return segments
    
    def segments_to_ranges(self, segments):
        ranges = []

        for seg in segments:
            ranges.append({
                "start": seg[0]["start"],
                "end": seg[-1]["end"]
            })

        return ranges
    
    def ranges_to_cut_points(self,ranges):
        cuts = []

        for i in range(len(ranges) - 1):
            cuts.append(ranges[i]["end"])
            cuts.append(ranges[i+1]["start"])

        return cuts

    def _prepare_output_directory(self, node_state: NodeState, inputs: Dict[str, Any]) -> Path:
        artifact_id = node_state.artifact_id
        session_id = node_state.session_id
        output_directory = self.server_cache_dir / session_id / artifact_id
        output_directory.mkdir(parents=True, exist_ok=True)
        return output_directory
    
    def _format_clip_id(self, clip_index: int) -> str:
        return f"clip_{clip_index:0{CLIP_ID_NUMBER_WIDTH}d}"
