# OpenAI-Assistants-Streamllit-UI
A basic streamlit UI with pydantic classes for consuming API calls from the new OpenAI assistants API

![we get rate limited an awful lot these days](/img/rate_limit.png)

## Quick Start

1. Create a .env file (can use the sample as a template) with your OpenAI API key, a name for your assistant, and an optional description

2. Initialize your virtual environment with poetry. If you have not already installed poetry, you can do so with:
```
pip install poetry
```

and then run:

```
poetry init
```

3. Create the assistant by running `make-assistant.py`:
```
poetry run python make-assistant.py
```

You can also create the assistant yourself through the [OpenAI Assistant Playground](https://platform.openai.com/assistants) and copy/paste your Assistant info into .env manually.

![Configs for assistants in the ui](/img/make-assistant.png)

4. Run the program through streamlit:
```
poetry run streamlit run bot-ui.py
```

## Features:

### Assistants Beta with Threads and Runs

Leverages the new Assistant API to create and interact with OpenAI Assistants. Also uses their threads and runs endpoints to keep track of state and tool use.

### Custom tools

Gives agents a tool to send a set of buttons to the chat. Very useful!


### Handle whatever user inputs

Because we have the power of (cheaper) GPT4.5-Turbo, the Assistant can handle most anything users throw at it. Tons of fun!

## TODO:

- [ ] More tools for bot message types:
    - [ ] Dropdowns
    - [ ] Images
    - [ ] Carousels
- [ ] Add DALLE-3 tool when it is available
- [ ] Save quiz questions and answers