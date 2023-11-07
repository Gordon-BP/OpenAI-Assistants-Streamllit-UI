# OpenAI-Assistants-Streamllit-UI
A basic streamlit UI with pydantic classes for consuming API calls from the new OpenAI assistants API

## Quick Start

1. Create a .env file (can use the sample as a template) with your OpenAI API key

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

4. Run the program through streamlit:
```
poetry run streamlit run bot-ui.py
```