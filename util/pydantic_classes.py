from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime, timezone
from nanoid import generate
from typing import List, Dict, Any, Union


class Choice(BaseModel):
    """
    Represents a single choice item with a label for display and an actual value.

    Attributes:
        label (str): Display label for the choice.
        value (str): Actual value of the choice.
    """

    label: str = Field("", description="Display label for the choice")
    value: str = Field("", description="Actual value of the choice")


class BotButtonMessage(BaseModel):
    """
    Represents a message that contains buttons for the user to choose from.

    Attributes:
        text (str): Text to display above the buttons.
        choices (List[Choice]): List of choices for agent reply.
    """

    text: str = Field("", description="Text to show to the user above the buttons")
    choices: List[Choice] = Field(..., description="List of choices for agent reply")
    active: bool = Field(
        True, description="Whether or not the button should be clickable"
    )


class BotDropdownMessage(BaseModel):
    """
    Represents a message that contains a dropdown menu for the user.

    Attributes:
        text (str): Text to display above the dropdown.
        choices (List[Choice]): List of choices for agent reply.
    """

    text: str = Field("", description="Text to show to the user above the dropdown")
    choices: List[Choice] = Field([], description="List of choices for agent reply")
    active: bool = Field(
        True, description="Whether or not the button should be clickable"
    )


class BotHTMLMessage(BaseModel):
    """
    Represents a message that contains HTML content.

    Attributes:
        html (str): HTML string to be rendered for the user.
    """

    html: str = Field("", description="A string of HTML to be rendered for the user")


class BotImageMessage(BaseModel):
    """
    Represents a message that contains an image.

    Attributes:
        url (str): The hosted URL of the image.
    """

    url: str = Field("", description="The image's hosted URL")


class BotTextMessage(BaseModel):
    """
    Represents a basic text message.

    Attributes:
        text (str): Text message content.
        useMarkdown (bool): Flag to determine if text should be rendered using markdown.
    """

    text: str = Field(
        "Hello World", description="A basic text message sent to the user"
    )
    useMarkdown: bool = Field(
        True, description="Whether or not to render text using markdown"
    )


class BotMessageTypes(Enum):
    """
    Enum defining the various types of bot messages.
    """

    text = "text"
    image = "image"
    html = "html"
    button = "button"
    dropdown = "dropdown"


BotPayload = Union[
    BotTextMessage,
    BotImageMessage,
    BotHTMLMessage,
    BotButtonMessage,
    BotDropdownMessage,
]


class BotMessage(BaseModel):
    """
    Represents the main structure of a bot message.

    Attributes:
        type (BotMessageTypes): Type of the message being sent.
        payload (BotPayload): Actual message content/data.
    """

    type: BotMessageTypes = Field(
        "text", description="What type of message is being sent"
    )
    payload: BotPayload = Field("Hello World", description="The message being send")


class Directions(Enum):
    """
    Enum defining the direction of an event.
    """

    incoming = "incoming"
    outgoing = "outgoing"


class Event(BaseModel):
    """
    The base object that gets passed around all the services, capturing event details and context.

    Attributes:
        userId (str): A unique identifier for the user.
        conversationId (str): A unique identifier for the conversation.
        id (str): A unique identifier for this event.
        sentOn (datetime): Timestamp when the event was sent.
        direction (Directions): Direction of the event (either incoming or outgoing).
        payload (Dict[str, Any]): Payload containing the text to be processed.
        botReply (List[BotMessage]): Agent's replies to the user.
    """

    @staticmethod
    def gen_userId():
        """Generate a unique user ID."""
        return generate(size=12)

    @staticmethod
    def gen_convId():
        """Generate a unique conversation ID."""
        return generate(size=14)

    @staticmethod
    def gen_eventId():
        """Generate a unique event ID."""
        return generate(size=18)


    userId: str = Field(
        default_factory=gen_userId, description="A unique identifier for the user"
    )
    conversationId: str = Field(
        default_factory=gen_convId,
        description="A unique identifier for the conversation",
    )
    id: str = Field(
        default_factory=gen_eventId, description="A unique identifier for this event"
    )
    sentOn: datetime = Field(
        default_factory=datetime.utcnow, description="Datetime when the event was sent"
    )
    direction: Directions = Field(
        "incoming", description="Direction of the event - incoming or outgoing"
    )
    payload: Dict[str, Any] = Field(
        {}, description="Payload containing the text to be processed"
    )
    botReply: List[BotMessage] = Field([], description="Agent's replies to the user")

    class Config:
        """Configuration for JSON serialization."""

        json_encoders = {
            datetime: lambda dt: dt.astimezone(timezone.utc).isoformat(),
        }