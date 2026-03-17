# polimind

An extensible Python toolkit for AI capabilities. Its current public OpenAI interface lives under `polimind.api.openai` and preserves the existing chat, history, multimodal, and metrics workflow.

## Features

- **Centralized Client**: Use a single `Client` to manage your connection and spawn multiple chat sessions.
- **Variadic Chat Interface**: Send multiple message components directly: `chat.chat("Text", Image("local.png"), "More text")`.
- **Node-Based History**: Every interaction is a node with an incremental ID.
- **Context Control**: Activate or deactivate conversation nodes by their ID to manage the model's window.
- **Enhanced Metrics**: Track token usage, models, and active nodes per request with built-in Pandas integration.
- **Multimodal Support**: Handle local images (auto-base64 encoding) and remote URLs seamlessly.
- **State Persistence**: Save `Chat` states and load them via the `Client` to resume sessions.
- **Deep Copy**: Create independent clones of your chat session.

## Installation

```bash
# Via Pip (once published)
pip install polimind

# From source
git clone https://github.com/artitzco/polimind.git
cd polimind
pip install .
```

## Quick Start

```python
from polimind.api.openai import Client, Image

# Initialize the main client
client = Client(api_key="your-api-key") # or use OPENAI_API_KEY env var

# Start a new chat session
chat = client.chat(model="gpt-4o-mini", system_prompt="You are a helpful assistant.")

# Basic Chat
response = chat.chat("Hello! What can you do?")
print(response)

# Multimodal Chat (Local and URL)
chat.chat(
    "Analyze these images:",
    Image("path/to/local_image.png"),
    "and also this one:",
    Image("https://example.com/image.jpg")
)

# Manage History
df_history = chat.history.to_dataframe()
chat.history.toggle(node_id=1, active=False) # Context management

# Persistence
chat.save("my_session.json")
new_chat_recovered = client.load_chat("my_session.json")
```

## Project Structure

- `src/polimind/`: Root package for the project.
- `src/polimind/api/openai/`: OpenAI integration exposed by the package.
  - `__init__.py`: Contains the `Client` factory and exports.
  - `core.py`: Contains the `Chat` session manager.
  - `history.py`: Logic for node-based conversation management.
  - `metrics.py`: Token usage and request tracking.
  - `content.py`: Multimodal data builders (Images, etc.).
- `notebooks/`: Interactive guides and testing playgrounds.
- `img/`: Storage for sample assets.
- `output/`: Default location for saved session JSONs.

## License

MIT
