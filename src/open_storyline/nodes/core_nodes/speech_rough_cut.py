from typing import Any, Dict
import os
import subprocess
import tempfile

from open_storyline.nodes.core_nodes.base_node import BaseNode, NodeMeta
from open_storyline.nodes.node_state import NodeState
from open_storyline.nodes.node_schema import LocalASRInput
from open_storyline.utils.register import NODE_REGISTRY

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

    input_schema = LocalASRInput

    def _load_asr_model(self):

        if hasattr(self, "asr_model"):
            return self.asr_model
        else:
            from funasr import AutoModel

            self.asr_model = AutoModel(
                model="paraformer-zh",
                vad_model="fsmn-vad",
                punc_model="ct-punc",
                vad_kwargs={"max_single_segment_time": 30000},
            )
            return self.asr_model
        

    async def default_process(
        self,
        node_state,
        inputs: Dict[str, Any],
    ) -> Any:
        return {}

    async def process(self, node_state: NodeState, inputs: Dict[str, Any]) -> Any:
        
        asr_infos = inputs["asr"].get('asr_infos', [])
        
    
    def _combine_tool_outputs(self, node_state, outputs):
        
        asr_infos = outputs.get("asr_infos", [])
        regularized_asr_infos = []

        for asr_info in asr_infos:
            clip_id = asr_info["clip_id"]
            kind = asr_info["kind"]
            asr_res = asr_info.get("asr_res", {})

            regularized_asr_infos.append({
                "clip_id": clip_id,
                "kind": kind,
                "asr_text": asr_res.get("text", "") if asr_res else "",
                "asr_timestamps": asr_res.get("timestamps", []) if asr_res else [],
                "asr_sentence_info": asr_res.get("sentence_info", []) if asr_res else [],
            })
        return {
            "asr_infos": regularized_asr_infos,
        }
