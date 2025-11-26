from __future__ import annotations

from typing import Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

from app.models.model_router import ModelRouter


def _format_entry(entry: Dict) -> str:
    filename = entry.get("filename", "unknown")
    summary = entry.get("high_level_summary") or entry.get("raw_summary") or ""
    key_points = entry.get("key_points") or entry.get("topics") or []
    objectives = entry.get("learning_objectives") or []
    lines = [f"File: {filename}"]
    if summary:
        lines.append(f"Summary: {summary}")
    if key_points:
        joined = "; ".join([str(item) for item in key_points])
        lines.append(f"Key Points: {joined}")
    if objectives:
        joined = "; ".join([str(item) for item in objectives])
        lines.append(f"Learning Objectives: {joined}")
    return "\n".join(lines)


def build_context(entries: List[Dict], max_entries: int = 8, max_chars: int = 16000) -> str:
    chunks: List[str] = []
    for entry in entries[:max_entries]:
        block = _format_entry(entry)
        if block:
            chunks.append(block)
        current_length = sum(len(c) for c in chunks)
        if current_length >= max_chars:
            break
    return "\n\n".join(chunks)


def build_langchain_chat_chain(final_entries: List[Dict]):
    context = build_context(final_entries)
    router = ModelRouter()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful tutor answering questions using the provided course knowledge."
                " Use the context below and cite filenames when helpful.\n\n{context}",
            ),
            ("user", "{question}"),
        ]
    )

    def _call_router(prompt_value):
        text_prompt = prompt_value.to_string()
        result = router.complete(prompt=text_prompt)
        return result.get("output_text", "")

    chain = (
        {
            "question": RunnablePassthrough(),
            "context": RunnableLambda(lambda _: context),
        }
        | prompt
        | RunnableLambda(_call_router)
        | StrOutputParser()
    )
    return chain
