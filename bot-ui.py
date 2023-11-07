import streamlit as st
from nanoid import generate
from typing import Dict
from pydantic_classes import (
    Event,
    BotMessageTypes,
    BotMessage,
    BotButtonMessage,
    BotTextMessage,
    Choice,
)
import json
import time
import openai
import os
from dotenv import load_dotenv
from logger import logger

load_dotenv()

st.title("Buzzfeed Quiz Generator!")
client = openai.Client(api_key=os.environ["OPENAI_API_KEY"])
with open('style.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def getBotResponse(userEvent: Event) -> Event:
    # Reverses the string, for now
    # In the future, calls the API
    event_dict = userEvent.model_dump()
    event_dict["userInput"] = event_dict["payload"]["text"]
    # event_dict["payload"] = {}
    run = client.beta.threads.runs.retrieve(
        run_id=st.session_state.runId,
        thread_id=st.session_state.threadId,
    )
    while run.status == "in_progress":
        logger.debug("Run in progress, waiting....")
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            run_id=st.session_state.runId,
            thread_id=st.session_state.threadId,
        )
        logger.debug(f"Current run status is {run.status}")
    if run.status == "requires_action":
        logger.debug("Run requires action!")
        # Turn the tool use into button class
        logger.debug(
            f"Run tool output id:\n{run.required_action.submit_tool_outputs.tool_calls[0].id}"
        )
        # call our new assistant
        client.beta.threads.runs.submit_tool_outputs(
            run_id=st.session_state.runId,
            thread_id=st.session_state.threadId,
            tool_outputs=[
                {
                    "tool_call_id": run.required_action.submit_tool_outputs.tool_calls[
                        0
                    ].id,
                    "output": str(event_dict["payload"]),
                }
            ],
        )
        run = client.beta.threads.runs.retrieve(
            run_id=st.session_state.runId, thread_id=st.session_state.threadId
        )
        while run.status == "in_progress":
            logger.debug("Submitted user input, waiting....")
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                run_id=st.session_state.runId,
                thread_id=st.session_state.threadId,
            )
            logger.debug(f"Current run status is {run.status}")
        logger.debug("Received stuff back from the assistant!")
        if run.status == "requires_action":
            logger.debug(
                f"Here is the returned obj from Assistant:\n{run.required_action.submit_tool_outputs.tool_calls[0]}"
            )
            asst_args = run.required_action.submit_tool_outputs.tool_calls[0]
            if asst_args:
                logger.debug(asst_args.function.arguments)
                data = json.loads(asst_args.function.arguments)
                text, choices = data["text"], data["choices"]
                event_dict["botReply"] = [
                    BotMessage(
                        type="button",
                        payload=BotButtonMessage(
                            text=text,
                            choices=[
                                Choice(label=n["label"], value=n["value"])
                                for n in choices
                            ],
                            active=True,
                        ),
                    ),
                ]
    if run.status == "completed":
        logger.debug("No required actions, I think...")
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.threadId
        )
        logger.debug(messages)
        logger.debug(type(messages))
        event_dict["botReply"] = [
            BotMessage(
                type="text",
                payload=BotTextMessage(
                    text=messages.data[0].content[0].text.value,
                    useMarkdown=True,
                ),
            ),
        ]
    if run.status == "failed":
        logger.debug(f"Run failed: {run.last_error.code}. {run.last_error.message}")
        event_dict["botReply"] = [
            BotMessage(
                type="text",
                payload=BotTextMessage(
                    text=f"Sorry, there was an error in the chat: {run.last_error.code}. {run.last_error.message}",
                    useMarkdown=True,
                ),
            ),
        ]
    event_dict["direction"] = "outgoing"
    botEvent = Event(**event_dict)
    return botEvent


def deactivateButtons() -> None:
    prevEvent = st.session_state.messages[-1]["content"]
    for reply in prevEvent.botReply:
        if reply.type == BotMessageTypes.button:
            reply.payload.active = False
    st.session_state.messages[-1]["content"] = prevEvent


def makeUserMessage(userInput: Dict[str, str] = {}) -> Event:
    if not userInput and st.session_state["userInput"]:
        userInput = {"type": "text", "text": st.session_state["userInput"]}
        logger.info(f"User pressed button: {st.session_state['userInput']}")
    else:
        logger.info(f"User said: {userInput['text']}")
    deactivateButtons()
    userEvent = Event(
        userId=st.session_state.userId,
        conversationId=st.session_state.conversationId,
        direction="incoming",
        payload=userInput,
    )
    st.session_state.messages.append({"role": "user", "content": userEvent})
    return userEvent


def makeButtons(payload: BotButtonMessage) -> st.delta_generator.DeltaGenerator:
    with st.chat_message("assistant") as msg:
        st.markdown(payload.text)
        # The idea is to format the columns like [1,1,1, 7] with a 1 for each choice
        # This needs to be replaced by a more robust auto-layout
        col_layout = [1] * len(payload.choices) + [6 - len(payload.choices)]
        cols = st.columns(col_layout)
        for i in range(len(cols) - 1):
            with cols[i]:
                st.button(
                    label=payload.choices[i].label,
                    key=generate(size=8),
                    disabled=not (payload.active),
                    on_click=makeUserMessage,
                    args=[{"type": "button", "text": payload.choices[i].value}],
                )
    return msg


def makeMarkdown(payload: BotTextMessage) -> st.delta_generator.DeltaGenerator:
    with st.chat_message("assistant") as msg:
        st.markdown(payload.text)
    return msg


def makeText(payload: BotTextMessage) -> st.delta_generator.DeltaGenerator:
    with st.chat_message("assistant") as msg:
        st.text(payload.text)
    return msg


def init_session_state():
    logger.debug("Initializing streamlit session...")
    thread = client.beta.threads.create(messages=[{"role": "user", "content": "Hello"}])
    assistant = client.beta.assistants.retrieve(assistant_id=os.environ.get("OPENAI_ASSISTANT_ID"))
    if "threadId" not in st.session_state:
        st.session_state.threadId = thread.id
    if "run" not in st.session_state:
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id
        )
        st.session_state.runId = run.id
    if "userId" not in st.session_state:
        st.session_state.userId = generate(size=12)
    if "conversationId" not in st.session_state:
        st.session_state.conversationId = generate(size=14)
    # init the OpenAI agent run
    run = client.beta.threads.runs.retrieve(
        run_id=st.session_state.runId, thread_id=st.session_state.threadId
    )
    logger.debug(run.status)
    # Wait for run to finish
    while run.status == "in_progress":
        logger.debug("Run intializing, waiting...")
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            run_id=st.session_state.runId, thread_id=st.session_state.threadId
        )
        logger.debug(run.status)
    # Add the first message
    if "messages" not in st.session_state:
        if run.status == "requires_action":
            logger.debug(f"Here is the returned obj from Assistant:\n{run}")
            asst_args = run.required_action.submit_tool_outputs.tool_calls[0]
            if asst_args:
                logger.debug(asst_args.function.arguments)
                data = json.loads(asst_args.function.arguments)
                text, choices = data["text"], data["choices"]
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": Event(
                        userId=st.session_state.userId,
                        conversationId=st.session_state.conversationId,
                        direction="outgoing",
                        botReply=[
                            BotMessage(
                                type="button",
                                payload=BotButtonMessage(
                                    text=text,
                                    choices=[
                                        Choice(label=n["label"], value=n["value"])
                                        for n in choices
                                    ],
                                    active=True,
                                ),
                            )
                        ],
                    ),
                }
            ]
        if run.status == "failed":
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": Event(
                        userId=st.session_state.userId,
                        conversationId=st.session_state.conversationId,
                        direction="outgoing",
                        botReply=[
                            BotMessage(
                                type="text",
                                payload=BotTextMessage(
                                    text=f"There was an error starting the chat: {run.last_error.code}. {run.last_error.message}",
                                    useMarkdown=True,
                                ),
                            )
                        ],
                    ),
                }
            ]


# Initialize messages with welcome message
if __name__ == "__main__":
    if "userId" not in st.session_state:
        with st.chat_message("assistant"):
            with st.spinner("Loading quiz..."):
                init_session_state()
                st.rerun()
    # Write messages to app
    for message in st.session_state.messages:
        if message["role"] != "user":
            for reply in message["content"].botReply:
                if reply.type == BotMessageTypes.button:
                    logger.debug("Writing bot button message to chat...")
                    makeButtons(reply.payload)
                if reply.type == BotMessageTypes.text:
                    if reply.payload.useMarkdown:
                        logger.debug("Writing bot markdown message to chat...")
                        makeMarkdown(reply.payload)
                    else:
                        logger.debug("Writing bot text message to chat...")
                        makeText(reply.payload)
        else:
            with st.chat_message("user"):
                logger.debug("Writing user message to chat...")
                st.markdown(message["content"].payload["text"])
    if st.session_state.messages[-1]["role"] != "assistant":
        logger.debug("Processing user input...")
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                botEvent = getBotResponse(st.session_state.messages[-1]["content"])
                st.session_state.messages.append(
                    {"role": "assistant", "content": botEvent}
                )
                st.rerun()
    logger.debug("Waiting for user input...")
    prompt = st.chat_input(
        "Type your response here", key="userInput", on_submit=makeUserMessage
    )
