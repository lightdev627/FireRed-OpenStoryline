import asyncio
import time
import uuid
import os,sys
import json

from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

# Add src directory to Python module search path
ROOT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.join(ROOT_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from open_storyline.agent import ClientContext, build_agent
from open_storyline.utils.prompts import get_prompt
from open_storyline.utils.media_handler import scan_media_dir
from open_storyline.config import load_settings, default_config_path
from open_storyline.storage.agent_memory import ArtifactStore
from open_storyline.mcp.hooks.node_interceptors import ToolInterceptor
from open_storyline.mcp.hooks.chat_middleware import PrintStreamingTokens

_MEDIA_STATS_INFO_IDX = 1

async def main():
    session_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    cfg = load_settings(default_config_path())
    
    artifact_store = ArtifactStore(cfg.project.outputs_dir, session_id=session_id)
    agent, node_manager = await build_agent(cfg=cfg, session_id=session_id, store=artifact_store, tool_interceptors=[ToolInterceptor.inject_media_content_before, ToolInterceptor.save_media_content_after, ToolInterceptor.inject_tts_config])

    context = ClientContext(
        cfg=cfg,
        session_id=session_id,
        media_dir=cfg.project.media_dir,
        bgm_dir=cfg.project.bgm_dir,
        outputs_dir=cfg.project.outputs_dir,
        node_manager=node_manager,
        chat_model_key=cfg.llm.model,
    )

    messages: List[BaseMessage] = [
        SystemMessage(content=get_prompt("instruction.system", lang='en')),
        SystemMessage(content="【User media statistics】{}"),
        ]

    print("Smart Editing Agent v 1.0.0")
    print("Please describe your editing needs, type /exit to exit.")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodBye~")
            break

        if not user_input:
            continue
        if user_input in ("/exit", "/quit"):
            print("\nGoodBye~")
            break

        media_stats = scan_media_dir(context.media_dir)
        messages[_MEDIA_STATS_INFO_IDX] = SystemMessage(
            content=(
                f"【User media statistics】{json.dumps(media_stats, ensure_ascii=False)}"
            )
        )
    
        messages.append(HumanMessage(content=user_input))
        
        print("Agent: ", end="", flush=True)

        stream = PrintStreamingTokens()

        result = await agent.ainvoke(
            {"messages": messages},
            context=context,
            config={"callbacks": [stream]},
        )

        print("\n")

        messages = result["messages"]

        final_text = None
        for m in reversed(messages):
            if isinstance(m, AIMessage):
                final_text = m.content
                break

        print(f"\nAgent: {final_text or '(No final response generated)'}\n")


if __name__ == "__main__":
    asyncio.run(main())
