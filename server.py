import asyncio
from typing import Annotated
import os
import random
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INVALID_PARAMS, INTERNAL_ERROR
from pydantic import BaseModel, Field

# --- Load environment variables ---
load_dotenv()

TOKEN = os.environ.get("AUTH_TOKEN")
MY_NUMBER = os.environ.get("MY_NUMBER")

assert TOKEN is not None, "Please set AUTH_TOKEN in your .env file"
assert MY_NUMBER is not None, "Please set MY_NUMBER in your .env file"

# --- Auth Provider ---
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(public_key=k.public_key, jwks_uri=None, issuer=None, audience=None)
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="hangman-client",
                scopes=["*"],
                expires_at=None,
            )
        return None

# --- Rich Tool Description model ---
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None = None

# --- Hangman Game Class ---
class HangmanGame:
    def __init__(self):
        # Array of words to choose from
        self.words = [
            "PYTHON", "JAVASCRIPT", "COMPUTER", "PROGRAMMING", "ALGORITHM",
            "DATABASE", "NETWORK", "SOFTWARE", "HARDWARE", "INTERNET",
            "FUNCTION", "VARIABLE", "BOOLEAN", "INTEGER", "STRING",
            "FRAMEWORK", "LIBRARY", "DEBUGGING", "COMPILER", "SYNTAX"
        ]
        
        # Hangman stick figure stages (6 wrong guesses allowed)
        self.hangman_stages = [
            """
   +---+
   |   |
       |
       |
       |
       |
=========
            """,
            """
   +---+
   |   |
   O   |
       |
       |
       |
=========
            """,
            """
   +---+
   |   |
   O   |
   |   |
       |
       |
=========
            """,
            """
   +---+
   |   |
   O   |
  /|   |
       |
       |
=========
            """,
            """
   +---+
   |   |
   O   |
  /|\\  |
       |
       |
=========
            """,
            """
   +---+
   |   |
   O   |
  /|\\  |
  /    |
       |
=========
            """,
            """
   +---+
   |   |
   O   |
  /|\\  |
  / \\  |
       |
=========
            """
        ]
        
        self.reset_game()
    
    def reset_game(self):
        """Start a new game"""
        self.current_word = random.choice(self.words)
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.max_wrong_guesses = 6
        self.game_over = False
        self.won = False
    
    def get_display_word(self):
        """Show the word with guessed letters revealed"""
        return " ".join([letter if letter in self.guessed_letters else "_" 
                        for letter in self.current_word])
    
    def make_guess(self, letter):
        """Make a guess and return the game state"""
        if self.game_over:
            return "Game is over! Start a new game."
        
        letter = letter.upper()
        
        # Check if letter was already guessed
        if letter in self.guessed_letters:
            return f"You already guessed '{letter}'. Try a different letter!"
        
        # Check if it's a valid single letter
        if len(letter) != 1 or not letter.isalpha():
            return "Please guess a single letter only!"
        
        # Add letter to guessed letters
        self.guessed_letters.add(letter)
        
        # Check if letter is in the word
        if letter in self.current_word:
            # Check if word is complete
            if all(letter in self.guessed_letters for letter in self.current_word):
                self.game_over = True
                self.won = True
        else:
            self.wrong_guesses += 1
            if self.wrong_guesses >= self.max_wrong_guesses:
                self.game_over = True
                self.won = False
        
        return self.get_game_status()
    
    def get_game_status(self):
        """Get current game status as a formatted string"""
        status = "```\n" + self.hangman_stages[self.wrong_guesses] + "```\n"
        status += f"Word: {self.get_display_word()}\n"
        status += f"Letters guessed: {', '.join(sorted(self.guessed_letters)) if self.guessed_letters else 'None'}\n"
        status += f"Wrong guesses: {self.wrong_guesses}/{self.max_wrong_guesses}\n"
        status += f"Remaining guesses: {self.max_wrong_guesses - self.wrong_guesses}\n\n"
        
        if self.game_over:
            if self.won:
                status += "🎉 **CONGRATULATIONS! YOU WON!** 🎉\n"
                status += f"The word was: **{self.current_word}**"
            else:
                status += "💀 **GAME OVER! YOU LOST!** 💀\n"
                status += f"The word was: **{self.current_word}**"
        else:
            status += "Keep guessing! Enter a letter... 🎯"
        
        return status

# --- Global game instance ---
game = HangmanGame()

# --- MCP Server Setup ---
mcp = FastMCP(
    "Hangman Game MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# --- Tool: validate (required by Puch) ---
@mcp.tool
async def validate() -> str:
    return MY_NUMBER

# --- Tool: start_new_game ---
StartGameDescription = RichToolDescription(
    description="Start a new hangman game with a random word",
    use_when="Use this when the user wants to start a new hangman game or restart the current one",
    side_effects="Resets the current game state and selects a new random word"
)

@mcp.tool(description=StartGameDescription.model_dump_json())
async def start_new_game() -> str:
    """Start a new hangman game"""
    game.reset_game()
    
    status = "🎮 **NEW HANGMAN GAME STARTED!** 🎮\n\n"
    status += game.get_game_status()
    status += f"\n\nHint: The word has {len(game.current_word)} letters and is related to programming/computers!"
    
    return status

# --- Tool: user_tool_make_guess ---
GuessDescription = RichToolDescription(
    description="Make a letter guess in the current hangman game",
    use_when="Use this when the user wants to guess a letter in the hangman game",
    side_effects="Updates the game state, reveals letters if correct, or adds to wrong guesses if incorrect"
)

@mcp.tool(description=GuessDescription.model_dump_json())
async def user_tool_make_guess(
    letter: Annotated[str, Field(description="The letter to guess (single character)")]
) -> str:
    """Make a guess in the hangman game"""
    if not hasattr(game, 'current_word') or not game.current_word:
        return "❌ No game in progress! Please start a new game first."
    
    letter = letter.upper().strip()
    
    # Check if already guessed
    if letter in game.guessed_letters:
        status = f"🎮 **HANGMAN GAME** 🎮\n\n"
        status += f"You already guessed '{letter}'!\n\n"
        status += game.get_game_status()
        return status
    
    # Check if letter is in word
    if letter in game.current_word:
        game.guessed_letters.add(letter)
        # Check if won
        if all(l in game.guessed_letters for l in game.current_word):
            game.game_over = True
            game.won = True
        
        status = f"🎮 **HANGMAN GAME** 🎮\n\n"
        status += f"✅ Great! '{letter}' is in the word!\n\n"
        status += game.get_game_status()
        return status
    else:
        game.guessed_letters.add(letter)
        game.wrong_guesses += 1
        if game.wrong_guesses >= game.max_wrong_guesses:
            game.game_over = True
            game.won = False
        
        status = f"🎮 **HANGMAN GAME** 🎮\n\n"
        status += f"❌ Sorry, '{letter}' is not in the word.\n\n"
        status += game.get_game_status()
        return status

# --- Tool: get_game_status ---
StatusDescription = RichToolDescription(
    description="Get the current status of the hangman game",
    use_when="Use this when the user wants to see the current game state without making a guess",
    side_effects="None - just displays current game information"
)

@mcp.tool(description=StatusDescription.model_dump_json())
async def get_game_status() -> str:
    """Get current game status"""
    if not hasattr(game, 'current_word') or not game.current_word:
        return "No game in progress! Please start a new game first."
    
    return f"🎮 **HANGMAN GAME STATUS** 🎮\n\n{game.get_game_status()}"

# --- Tool: game_rules ---
RulesDescription = RichToolDescription(
    description="Explain the rules of hangman game",
    use_when="Use this when the user wants to understand how to play hangman",
    side_effects="None - just provides information"
)

@mcp.tool(description=RulesDescription.model_dump_json())
async def game_rules() -> str:
    """Explain hangman game rules"""
    rules = """
🎮 **HANGMAN GAME RULES** 🎮

📝 **How to Play:**
1. I'll pick a random word related to programming/computers
2. You see blank spaces representing each letter: _ _ _ _ _
3. Guess letters one at a time
4. If your letter is in the word, it gets revealed in all positions
5. If your letter is NOT in the word, part of the hangman gets drawn
6. You have 6 wrong guesses before the hangman is complete

🎯 **How to Win:**
- Guess all letters in the word before making 6 wrong guesses

💀 **How to Lose:**
- Make 6 wrong guesses and the hangman drawing is completed

🎲 **Commands:**
- Use `start_new_game` to begin a new game
- Use `make_guess` with a letter to guess
- Use `get_game_status` to see current progress

Good luck! 🍀
    """
    return rules.strip()

# --- Run MCP Server ---
async def main():
    print("🎮 Starting Hangman MCP server on http://0.0.0.0:8086")
    await mcp.run_async("streamable-http", host="0.0.0.0", port=8086)

if __name__ == "__main__":
    asyncio.run(main())