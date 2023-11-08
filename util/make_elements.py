import streamlit as st
from nanoid import generate
from util.pydantic_classes import (
    BotMessage,
    BotImageMessage,
    BotButtonMessage,
    BotTextMessage,
)
from typing import Callable

def makeImage(payload: BotImageMessage)-> st.delta_generator.DeltaGenerator:
    """
    Displays an image message in the chat interface.

    Args:
    - payload: A BotImageMessage object containing the URL of the image to display.

    Returns:
    - A Streamlit DeltaGenerator object representing the chat message.
    """
    with st.container() as c:
        cols =st.cols([1,1]) #image should only take up half of total width
        with cols[0]:
            st.image(urls=payload.url, use_column_width=True)
    return c



def makeButtons(payload: BotButtonMessage, onClick:Callable) -> st.delta_generator.DeltaGenerator:
    """
    Displays a set of interactive buttons as part of a bot message in the chat interface.

    Args:
    - payload: A BotButtonMessage object containing the text and the choices for the buttons.

    Returns:
    - A Streamlit DeltaGenerator object representing the chat message.
    """
    with st.container() as c:
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
                    on_click=onClick,
                    args=[{"type": "button", "text": payload.choices[i].value}],
                )
    return c


def makeText(payload: BotTextMessage) -> st.delta_generator.DeltaGenerator:
    """
    Displays a plain text message in the chat interface.

    Args:
    - payload: A BotTextMessage object containing the text to display.

    Returns:
    - A Streamlit DeltaGenerator object representing the chat message.
    """
    with st.container() as c:
        st.text(payload.text)
    return c

def makeMarkdown(payload: BotTextMessage) -> st.delta_generator.DeltaGenerator:
    """
    Displays a markdown message in the chat interface.

    Args:
    - payload: A BotTextMessage object containing the markdown text to display.

    Returns:
    - A Streamlit DeltaGenerator object representing the chat message.
    """
    with st.container() as c:
        st.markdown(payload.text)
    return c
