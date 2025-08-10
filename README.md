# Developer Profile Roaster: Get Brutally Honest Feedback on Your Coding Journey

## 🔥 Tired of generic feedback? Need someone to tell you the harsh truth about your GitHub commits and LeetCode grind? This MCP doesn't sugarcoat anything!

**Developer Profile Roaster MCP** is your no-nonsense coding companion that fetches your GitHub and LeetCode profiles, analyzes your stats, and delivers brutally honest (but constructive) roasts about your developer journey. Whether you're grinding LeetCode with a terrible acceptance rate or have repos with zero stars, this tool will call you out while providing actionable advice to level up your game.

### ✨ Features

- **GitHub Profile Analysis**: Fetches comprehensive GitHub stats including repos, stars, followers, languages, and account activity
- **LeetCode Stats Tracking**: Analyzes your problem-solving journey with difficulty breakdowns and acceptance rates
- **AI-Powered Roasting**: Get savage but constructive feedback on your coding habits and online presence
- **Actionable Improvement Tips**: Receive concrete advice to enhance your developer profile and skills
- **Secure Authentication**: Bearer token authentication to keep your roasts private
- **Real-time Data**: Always fetches the latest stats from both platforms

### 🛠️ Available Tools

1. **`get_github_profile_data`**: Analyzes GitHub profiles with comprehensive stats and social media presence
2. **`get_leetcode_profile_data`**: Fetches LeetCode problem-solving statistics and performance metrics
3. **`validate`**: Authentication validation tool

### 🎯 Perfect For

- Developers who want honest feedback about their coding journey
- Job seekers looking to improve their GitHub profile before interviews
- Competitive programmers tracking their LeetCode progress
- Anyone brave enough to face the truth about their coding habits

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- GitHub account (for profile analysis)
- LeetCode account (optional, for coding challenge stats)

### Installation

```bash
# Clone the repository
git clone https://github.com/ayush18pop/puch.ai-hackathon

# Navigate to project directory
cd puch.ai-hackathon

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
AUTH_TOKEN=your_secure_bearer_token_here
MY_NUMBER=your_validation_number_here
```

### Running the Server

```bash
python server.py
```

The MCP server will start on `http://0.0.0.0:8086`

## 📊 Usage Examples

### Analyzing a GitHub Profile

```python
# Fetch comprehensive GitHub stats
profile_data = await get_github_profile_data("octocat")

# Returns detailed analysis including:
# - Repository count and star distribution
# - Follower/following ratios
# - Top programming languages
# - Account age and activity patterns
# - Twitter/X integration
# - AI-generated roast and improvement tips
```

### LeetCode Performance Review

```python
# Get brutal feedback on your LeetCode journey
leetcode_stats = await get_leetcode_profile_data("username")

# Analyzes:
# - Problem-solving distribution (Easy/Medium/Hard)
# - Acceptance rates and ranking
# - Performance compared to other users
# - Personalized grind plan for improvement
```

## 🔗 Project Links

- **GitHub Repository**: [https://github.com/ayush18pop/puch.ai-hackathon](https://github.com/ayush18pop/puch.ai-hackathon)
- **Social Media**: Share your roasting experience with #BuildWithPuch

## 🏗️ Built With

- **FastMCP**: High-performance MCP server framework
- **Python 3.11+**: Core development language
- **HTTPX**: Async HTTP client for API requests
- **Pydantic**: Data validation and serialization
- **GitHub API**: Real-time repository and profile data
- **LeetCode GraphQL API**: Problem-solving statistics

## 🤝 Contributing

Found a bug or want to add more roasting features? Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-roast`)
3. Commit your changes (`git commit -m 'Add even more savage roasts'`)
4. Push to the branch (`git push origin feature/amazing-roast`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## ⚠️ Disclaimer

This tool provides brutally honest feedback for educational and motivational purposes. All roasts are generated in good fun to help developers improve their skills. Remember: every expert was once a beginner, and every failure is a step toward success!

---

_Built during the Puch.AI Hackathon - where developers come to get roasted and leave motivated! 🔥_
