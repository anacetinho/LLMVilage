# Village AI Demo - Pokemon-Style Top-Down Game

A top-down village game with AI-powered villagers that can respond to player interactions using a local language model.

## Features

- **Pokemon-style gameplay**: Top-down view with sprite-based characters
- **AI-powered villagers**: Each villager has unique backstories and responds using LM Studio's Mistral model
- **Interactive village**: 3 houses, trees, and wandering villagers
- **Player actions**:
  - Movement: Arrow keys or WASD
  - Talk: E key (opens dialog with text input)
  - Attack: P key (reduces villager HP)
- **Villager behaviors**:
  - Random walking around the village
  - Following the player when instructed
  - Fleeing when health is low (≤4 HP)
  - Remembering past interactions
  - Responding to commands like "go to house X", "follow me"

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up LM Studio**:
   - Install LM Studio from https://lmstudio.ai/
   - Download the "mistral-nemo-instruct-2407" model
   - Start the local server at http://127.0.0.1:1234
   - Make sure the API is accessible

3. **Run the game**:
   ```bash
   python main.py
   ```

## Controls

- **Arrow Keys/WASD**: Move player character
- **E**: Talk to villager in front of you
- **P**: Attack villager in front of you
- **ESC**: Close dialog box
- **Enter**: Send message in dialog

## Villager Commands

When talking to villagers, you can give them commands:
- "follow me" - Villager will follow the player
- "stop following" - Stop following the player
- "go to house 1/2/3" - Navigate to specific house
- General conversation - Free-form chat with AI responses

## Game Mechanics

- **Villagers start with 10 HP**
- **At 4 HP or below**: Villagers flee and seek help
- **At 0 HP**: Villagers are defeated
- **Memory system**: Villagers remember interactions
- **Collision detection**: Can't walk through houses/trees
- **Real-time AI**: Responses generated using local LM Studio

## Villager Characters

1. **Alice**: Friendly baker who loves recipes
2. **Bob**: Grumpy blacksmith with a good heart
3. **Carol**: Curious young scholar
4. **Dave**: Laid-back farmer

Each villager has unique personality traits and will respond accordingly to player interactions.