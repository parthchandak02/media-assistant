# Media Article Writer

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/parthchandak02/media-assistant)

**Generate professional, research-backed articles in minutes.** AI agents research your topic, write in your chosen publication style, and format everything perfectly—ready for scientific journals, tech news sites, or research magazines.

## Quick Start

**Prerequisites:** Python 3.10+ and [uv](https://github.com/astral-sh/uv#installation) package manager

```bash
# 1. Clone and install
git clone https://github.com/parthchandak02/media-assistant.git
cd media-assistant
uv sync

# 2. Configure API keys
cp .env.example .env
# Edit .env and add your keys (see API Keys section below)

# 3. Generate your first article
uv run python -m src.main --topic "Your research topic" --media-type tech_news
```

Your article will be saved in `outputs/` directory.

## API Keys

You need **one LLM provider** and **one search provider**:

**LLM (choose one):**
- `GEMINI_API_KEY` - [Get from Google AI Studio](https://aistudio.google.com/app/apikey)
- `PERPLEXITY_API_KEY` - [Get from Perplexity](https://www.perplexity.ai/settings/api)

**Search (choose one):**
- `EXA_API_KEY` - [Get from Exa](https://dashboard.exa.ai/)
- `GOOGLE_API_KEY` + `GOOGLE_CSE_ID` - [Get from Google Custom Search](https://developers.google.com/custom-search/v1/overview)

## Usage Examples

```bash
# Tech news style (TechCrunch, Wired)
uv run python -m src.main --topic "New AI safety framework" --media-type tech_news

# Research magazine style (Scientific American, Quanta)
uv run python -m src.main --topic "Quantum computing breakthrough" --media-type research_magazine

# Scientific journal style (Nature, Science)
uv run python -m src.main --topic "Novel protein folding approach" --media-type scientific_journal --length long
```

### With Context File (Better Results)

Create `my_context.json`:
```json
{
  "novel_aspect": "What makes your approach unique",
  "technology_details": "Technical details and methodology",
  "problem_solved": "What problem does this solve",
  "use_cases": "Specific examples or applications"
}
```

Then use it:
```bash
uv run python -m src.main --topic "Your topic" --media-type tech_news --context-file my_context.json
```

## What You Get

Articles are saved as markdown files in `outputs/` with:
- **Metadata header** (YAML frontmatter with title, date, topic)
- **Structured sections** (varies by media type)
- **Source citations** (automatically found, deduplicated, and formatted)

## Media Types

| Type | Style | Best For |
|------|-------|----------|
| `tech_news` | TechCrunch, Wired, The Verge | Technology announcements, innovation stories |
| `research_magazine` | Scientific American, Quanta | Popular science, research highlights |
| `scientific_journal` | Nature, Science, Cell | Academic research articles |
| `academic_news` | Inside Higher Ed | Academic achievements, institutional news |

## Configuration

Copy `config.yaml.example` to `config.yaml` and adjust settings:

```yaml
llm:
  provider: "gemini"  # or "perplexity"
  model: "gemini-2.5-flash"

search:
  provider: "exa"  # or "google" or "crewai"
  max_results: 10

article:
  media_type: "research_magazine"
  length: "medium"  # short, medium, or long
```

Most users only need to set `llm.provider` and `search.provider` to match their API keys. Everything else works with defaults.

## All Options

```bash
uv run python -m src.main [OPTIONS]

Required:
  --topic TEXT              Topic or achievement to write about

Options:
  --media-type TEXT         scientific_journal | research_magazine | 
                            tech_news | academic_news
  --length TEXT             short (500-800) | medium (1000-1500) | 
                            long (2000+)
  --context-file PATH       JSON file with your innovation details
  --output PATH             Custom output file path
  --verbose, -v             Show detailed progress
  --config PATH             Custom config file (default: config.yaml)
```

## Troubleshooting

**"Missing API keys" error**
- Check `.env` file exists and has correct key names
- Verify keys are valid (test them on provider websites)

**"Config error"**
- Make sure `config.yaml` exists (copy from `config.yaml.example`)
- Check YAML syntax (no tabs, proper indentation)

**"No results found"**
- Try a different search provider in `config.yaml`
- Check your search API key is valid
- Verify API quota hasn't been exceeded

**Article quality issues**
- Use `--context-file` to provide more details about your innovation
- Try different `media_type` for better style match
- Use `--verbose` to see what's happening

## How It Works

The system uses a **4-agent pipeline**:

1. **Research Agent** - Generates search queries and finds relevant sources
2. **Writer Agent** - Generates article sections following your chosen style
3. **Editor Agent** - Reviews for quality, consistency, and tone
4. **Humanizer Agent** - Makes writing sound natural and human-authored

## Advanced Usage

### Customizing Tones and Templates

Edit `src/config/tones.yaml` and `src/config/templates.yaml` to modify writing styles and article structures.

### Using CrewAI Search

```bash
pip install crewai crewai-tools
```

Then set `search.provider: "crewai"` in `config.yaml`.

## Project Structure

```
media-article-writer/
├── src/
│   ├── agents/           # Research, Writer, Editor, Humanizer agents
│   ├── config/           # Tones and templates
│   ├── utils/            # Helpers (LLM, search, formatting)
│   ├── pipeline.py       # Main orchestrator
│   └── main.py          # CLI entry point
├── tests/                # Test suite
├── outputs/             # Generated articles (gitignored)
├── config.yaml.example  # Configuration template
├── .env.example         # Environment variables template
└── README.md            # This file
```

## FAQ

**Q: How long does it take to generate an article?**  
A: Typically 1-3 minutes depending on search results and article length.

**Q: Can I edit the generated article?**  
A: Yes! Articles are saved as markdown files you can edit in any text editor.

**Q: Are sources automatically cited?**  
A: Yes, sources are automatically found, deduplicated, cleaned, and formatted.

**Q: How do I improve article quality?**  
A: Use `--context-file` to provide detailed information about your innovation. The more context, the better the article.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details (or check the repository).

---

**Repository**: [https://github.com/parthchandak02/media-assistant](https://github.com/parthchandak02/media-assistant)
