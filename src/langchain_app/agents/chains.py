"""Composable LangChain runnables for each agent role."""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .prompts import (
    FEEDBACK_SYSTEM_PROMPT,
    NL2SQL_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
)
from ..settings import LangChainAppSettings


def build_chat_model(settings: LangChainAppSettings) -> ChatOpenAI:
    """Instantiate the shared ChatOpenAI model used by every agent."""

    return ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.openai_api_key,
        temperature=0.0,
    )


def build_planner_chain(model: ChatOpenAI) -> StrOutputParser:
    """Return a runnable that produces an execution plan."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PLANNER_SYSTEM_PROMPT),
            ("human", "User question: {question}"),
            ("human", "Retrieved context:\n{context}"),
        ]
    )
    return prompt | model | StrOutputParser()


def build_sql_chain(model: ChatOpenAI) -> StrOutputParser:
    """Return a runnable that converts natural language into SQL."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", NL2SQL_SYSTEM_PROMPT),
            ("human", "Original question: {question}"),
            ("human", "Planning notes: {plan}"),
            ("human", "Retrieved context:\n{context}"),
        ]
    )
    return prompt | model | StrOutputParser()


def build_feedback_chain(model: ChatOpenAI) -> StrOutputParser:
    """Return a runnable that critiques the generated SQL query."""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", FEEDBACK_SYSTEM_PROMPT),
            ("human", "Original question: {question}"),
            ("human", "Planning notes: {plan}"),
            ("human", "Candidate SQL query:\n{sql_query}"),
            ("human", "Retrieved context:\n{context}"),
        ]
    )
    return prompt | model | StrOutputParser()
