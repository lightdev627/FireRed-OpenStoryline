from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set


from langchain_core.tools.structured import StructuredTool

from src.open_storyline.storage.agent_memory import ArtifactStore


class NodeManager:
    def __init__(self, tools: List[StructuredTool] = None):
        self.kind_to_node_ids: Dict[str, List[str]] = defaultdict(list)  # node_kind -> list of node_ids (sorted)
        self.id_to_tool: Dict[str, StructuredTool] = {}  # node_id -> StructuredTool
        self.id_to_next: Dict[str, List[str]] = {}  # node_id -> list of next executable node_ids
        self.id_to_priority: Dict[str, int] = {}  # node_id -> priority
        self.id_to_kind: Dict[str, str] = {}  # node_id -> node_kind
        
        # New: Prerequisite dependency related
        self.id_to_require_prior_kind: Dict[str, List[str]] = {}  # node_id -> required prerequisite features when executing auto method
        self.id_to_default_require_prior_kind: Dict[str, List[str]] = {}  # node_id -> prerequisite features needed for default method execution
        
        # Reverse index: which nodes depend on a specific kind
        self.kind_to_dependent_nodes: Dict[str, Set[str]] = defaultdict(set)  # kind -> set of node_ids that depend on this feature
        self.kind_to_default_dependent_nodes: Dict[str, Set[str]] = defaultdict(set)  # kind -> set of node_ids whose default method depends on this feature

        if tools:
            self._build(tools)
    
    def _build(self, tools: List[StructuredTool]):
        for tool in tools:
            if tool.metadata:
                metadata = tool.metadata.get('_meta', {})
                node_id = metadata.get('node_id')
                if node_id:
                    self.add_node(tool)
    
    def add_node(self, tool: StructuredTool) -> bool:
        # metadata is None, failed to add node 
        if not tool.metadata:
            return False
        
        metadata = tool.metadata.get('_meta', {})
        node_id = metadata.get('node_id')
        
        if not node_id:
            return False
        
        if node_id in self.id_to_tool:
            self.remove_node(node_id)
        
        node_kind = metadata.get('node_kind', node_id)
        priority = metadata.get('priority', 0)
        next_nodes = metadata.get('next_available_node', [])
        require_prior_kind = metadata.get('require_prior_kind', [])
        default_require_prior_kind = metadata.get('default_require_prior_kind', [])
        
        # Update dependencies
        self.id_to_tool[node_id] = tool
        self.id_to_priority[node_id] = priority
        self.id_to_next[node_id] = next_nodes
        self.id_to_kind[node_id] = node_kind
        self.id_to_require_prior_kind[node_id] = require_prior_kind
        self.id_to_default_require_prior_kind[node_id] = default_require_prior_kind
        
        # Add to kind_to_node_ids and re-sort
        self.kind_to_node_ids[node_kind].append(node_id)
        self._sort_kind(node_kind)
        
        # Update reverse index
        for kind in require_prior_kind:
            self.kind_to_dependent_nodes[kind].add(node_id)
        
        for kind in default_require_prior_kind:
            self.kind_to_default_dependent_nodes[kind].add(node_id)
        
        return True
    
    def remove_node(self, node_id: str, clean_references: bool = True) -> bool:
        """
        Delete a node, not used for the time being.
        
        Args:
            node_id: ID of the node to delete
            clean_references: Whether to clean up references to this node from other nodes
        """

        if node_id not in self.id_to_tool:
            return False
        
        node_kind = self.id_to_kind[node_id]
        
        # Clean up reverse index
        if node_id in self.id_to_require_prior_kind:
            for kind in self.id_to_require_prior_kind[node_id]:
                self.kind_to_dependent_nodes[kind].discard(node_id)
                if not self.kind_to_dependent_nodes[kind]:
                    del self.kind_to_dependent_nodes[kind]
        
        if node_id in self.id_to_default_require_prior_kind:
            for kind in self.id_to_default_require_prior_kind[node_id]:
                self.kind_to_default_dependent_nodes[kind].discard(node_id)
                if not self.kind_to_default_dependent_nodes[kind]:
                    del self.kind_to_default_dependent_nodes[kind]
        
        del self.id_to_tool[node_id]
        del self.id_to_priority[node_id]
        del self.id_to_next[node_id]
        del self.id_to_kind[node_id]
        
        if node_id in self.id_to_require_prior_kind:
            del self.id_to_require_prior_kind[node_id]
        if node_id in self.id_to_default_require_prior_kind:
            del self.id_to_default_require_prior_kind[node_id]
        
        # Remove from kind group
        if node_id in self.kind_to_node_ids[node_kind]:
            self.kind_to_node_ids[node_kind].remove(node_id)
        
        # If no nodes left for this kind, remove the kind
        if not self.kind_to_node_ids[node_kind]:
            del self.kind_to_node_ids[node_kind]
        
        # Remove references to this node in other nodes
        if clean_references:
            for nid in list(self.id_to_next.keys()):
                if node_id in self.id_to_next[nid]:
                    self.id_to_next[nid].remove(node_id)
        
        return True
    
    
    def _sort_kind(self, kind: str):
        """Sort node list for specified kind by priority"""
        if kind in self.kind_to_node_ids:
            self.kind_to_node_ids[kind].sort(
                key=lambda nid: self.id_to_priority[nid],
                reverse=True
            )
    
    def get_tool(self, node_id: str) -> Optional[StructuredTool]:
        """Get tool by node_id"""
        return self.id_to_tool.get(node_id)
    
    def check_excutable(self, session_id:str, store: ArtifactStore, all_require_kind: List[str]) -> Dict[str, Any]:
        """
        Check if executable and return unexecuted features
        """
        collected_output = {}
        for req_kind in all_require_kind:
            req_ids_queue = self.kind_to_node_ids[req_kind]
            # 1. Collect latest outputs from all nodes
            valid_outputs = []
            for node_id in req_ids_queue:
                output = store.get_latest_meta(node_id=node_id, session_id=session_id)
                if output is not None:
                    valid_outputs.append(output)

            # 2. Identify the most recently created output
            if valid_outputs:
                latest_output = max(valid_outputs, key=lambda output: output.created_at)
                collected_output[req_kind] = latest_output
        return {
            "excutable": len(collected_output.keys())==len(all_require_kind),
            "collected_node": collected_output,
            "missing_kind": list(set(all_require_kind) - set(collected_output.keys()))
        }
    
