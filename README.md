# OpenAI-Assistants-Streamllit-UI
A basic streamlit UI with pydantic classes for consuming API calls from the new OpenAI assistants API

![we get rate limited an awful lot these days](/img/rate_limit.png)

## 😅 The poor servers are under a lot of load right now, people are excited


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

If you want to change how things look, modify `./streamlit/config.toml`. You can also change and edit the theme in the streamlit UI by clicking the three dots in the upper right corner and going to "settings"

![This is where the three dots are](/img/settings.png)

![This is where the theme selection is](/img/edit_theme.png)

## Features:

### Assistants Beta with Threads and Runs

Leverages the new [Assistant API](https://platform.openai.com/docs/api-reference/assistants) to create and interact with OpenAI Assistants. Also uses their [threads](https://platform.openai.com/docs/api-reference/threads) and [runs](https://platform.openai.com/docs/api-reference/runs) endpoints to keep track of state and tool use.

### Custom tools

[Gives agents a tool](https://platform.openai.com/docs/assistants/tools) to send a set of buttons to the chat. Very useful!


### Pydantic Classes and Type Hints

Includes pydantic classes for all data types, type hints everywhere, and docstrings on all functions.

## TODO:

- [ ] More tools for bot message types:
    - [ ] Dropdowns
    - [ ] Images
    - [ ] Carousels
- [ ] Add DALLE-3 tool when it is available
- [ ] Save quiz questions and answers