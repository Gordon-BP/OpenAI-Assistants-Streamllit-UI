import streamlit as st
from nanoid import generate
from typing import Dict
from util.pydantic_classes import (
    Event,
    BotMessageTypes,
    BotMessage,
    BotButtonMessage,
    BotImageMessage,
    BotTextMessage,
    Choice,
)
from util.make_elements import (
    makeButtons,
    makeImage,
    makeMarkdown,
    makeText,
)
import json
import time
import openai
import os
from dotenv import load_dotenv
from util.logger import logger

load_dotenv()

if os.environ.get("OPENAI_ASSISTANT_NAME"):
    st.title(os.environ.get("OPENAI_ASSISTANT_NAME"))
if os.environ.get("QUIZ_DESCRIPTION"):
    st.markdown(os.environ.get("QUIZ_DESCRIPTION"))
client = openai.Client(api_key=os.environ["OPENAI_API_KEY"])

def getBotResponse(userEvent: Event) -> Event:
    """
    Retrieves the bot response for a given user event.

    This function uses the new assistants endpoints to get bot response.

    Args:
    - userEvent: An Event object that contains the user's input.

    Returns:
    - Event: An Event object containing the bot's response.
    """
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
            #TODO Add logic to switch between making buttons and making images
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
        logger.debug("No required actions, sending messages...")
        messages = client.beta.threads.messages.list(
            thread_id=st.session_state.threadId
        )
        logger.debug(messages)
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
    """
    Deactivates buttons in the most recent message in the session state.

    This function iterates over the last event's bot replies and deactivates any buttons found.
    """
    prevEvent = st.session_state.messages[-1]["content"]
    for reply in prevEvent.botReply:
        if reply.type == BotMessageTypes.button:
            reply.payload.active = False
    st.session_state.messages[-1]["content"] = prevEvent


def makeUserMessage(userInput: Dict[str, str] = {}) -> Event:
    """
    Creates a user message event from the given input and updates the session state.

    Args:
    - userInput: A dictionary containing the user's input text, if available.

    Returns:
    - Event: An Event object representing the user's message.
    """
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

def init_session_state():
    """
    Initializes the Streamlit session state with necessary values.

    This includes creating a new thread and run for the OpenAI assistant,
    generating a new user ID and conversation ID, and preparing the first message.
    """
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
                    makeButtons(reply.payload, makeUserMessage)
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
        "Type your response here", key="userInput", on_submit=makeUserMessage,
    )
