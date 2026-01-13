# Media Article Writer

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/parthchandak02/media-assistant)

**Generate professional, research-backed news articles in minutes.** This tool uses AI agents to research your topic, write in your chosen publication style, and format everything perfectly—ready to submit to scientific journals, tech news sites, or research magazines.

## What It Does

Turn any research topic or achievement into a professionally formatted article:
- **Research-backed**: Automatically finds and cites relevant sources
- **Style-matched**: Writes in the tone of Nature, Scientific American, TechCrunch, etc.
- **Publication-ready**: Clean markdown output with proper formatting
- **Fully automated**: 4-agent system (Research → Write → Edit → Humanize) handles everything

## Prerequisites

- **Python 3.10+** (check with `python --version`)
- **uv** package manager ([install uv](https://github.com/astral-sh/uv#installation))
  - macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - Or via pip: `pip install uv`

## Quick Start (3 Steps)

### 1. Install & Setup

```bash
# Clone the repository
git clone https://github.com/parthchandak02/media-assistant.git
cd media-assistant

# Install dependencies (creates virtual environment automatically)
uv sync

# That's it! uv manages the virtual environment for you
```

**Note**: If you don't have `uv` installed, see [Prerequisites](#prerequisites) above.

### 2. Configure API Keys

Create `.env` file with your API keys:

```bash
cp .env.example .env
# Edit .env and add your keys
```

**You need:**
- **LLM**: `GEMINI_API_KEY` OR `PERPLEXITY_API_KEY` (choose one)
- **Search**: `EXA_API_KEY` OR (`GOOGLE_API_KEY` + `GOOGLE_CSE_ID`)

Get keys:
- Gemini: https://aistudio.google.com/app/apikey
- Perplexity: https://www.perplexity.ai/settings/api
- Exa: https://dashboard.exa.ai/
- Google: https://developers.google.com/custom-search/v1/overview

### 3. Generate Your First Article

```bash
uv run python -m src.main \
  --topic "Your research topic or achievement" \
  --media-type tech_news
```

That's it! Your article will be saved in `outputs/` directory.

## Usage Examples

### Basic Article Generation

```bash
# Tech news style (TechCrunch, Wired)
uv run python -m src.main --topic "New AI safety framework" --media-type tech_news

# Research magazine style (Scientific American, Quanta)
uv run python -m src.main --topic "Quantum computing breakthrough" --media-type research_magazine

# Scientific journal style (Nature, Science)
uv run python -m src.main --topic "Novel protein folding approach" --media-type scientific_journal --length long

# Academic news style
uv run python -m src.main --topic "Award-winning research contribution" --media-type academic_news
```

### With Context File (Recommended)

Provide detailed context about your innovation for better articles:

**1. Create a context file** (`my_context.json`):
```json
{
  "novel_aspect": "What makes your approach unique",
  "technology_details": "Technical details and methodology",
  "problem_solved": "What problem does this solve",
  "use_cases": "Specific examples or applications",
  "confidential_info": "What NOT to mention (optional)",
  "additional_notes": "Any other relevant info (optional)"
}
```

**2. Use it:**
```bash
uv run python -m src.main \
  --topic "Your topic" \
  --media-type tech_news \
  --context-file my_context.json \
  --verbose
```

### With Verbose Output

See detailed progress and operations:

```bash
uv run python -m src.main \
  --topic "Your topic" \
  --media-type research_magazine \
  --verbose
```

This shows:
- Search queries being executed
- Results found per query
- Article sections being generated
- Source processing details

### All Options

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

## What You Get

### Article Structure

Your article includes:

1. **Metadata Header** (YAML frontmatter):
   ```yaml
   ---
   title: Your Article Headline
   date: 2026-01-13
   media_type: tech_news
   topic: Your Topic
   ---
   ```

2. **Structured Sections** (varies by media type):
   - Tech News: Headline, Opening, The Story, Why It Matters, What Next
   - Research Magazine: Headline, Lead, Background, Discovery, Impact, Future
   - Scientific Journal: Abstract, Introduction, Methods, Results, Discussion, Conclusion
   - Academic News: Headline, Lead, Achievement, Significance, Context

3. **Source Citations**:
   ```markdown
   ## Sources
   
   1. [Source Title](https://example.com)
      Relevant snippet from the source...
   
   2. [Another Source](https://example.com)
      Another relevant snippet...
   ```

### Output File

Articles are saved as markdown files in `outputs/` directory:
- Filename format: `{date}_{topic}_{media_type}.md`
- Ready to edit, submit, or convert to other formats
- Clean formatting, no HTML clutter
- Properly deduplicated and validated sources

## Media Types

| Type | Style | Best For |
|------|-------|----------|
| **tech_news** | TechCrunch, Wired, The Verge | Technology announcements, innovation stories |
| **research_magazine** | Scientific American, Quanta | Popular science, research highlights |
| **scientific_journal** | Nature, Science, Cell | Academic research articles |
| **academic_news** | Inside Higher Ed | Academic achievements, institutional news |

## Configuration

### Basic Config (`config.yaml`)

Copy `config.yaml.example` to `config.yaml`:

```yaml
llm:
  provider: "gemini"  # or "perplexity"
  model: "gemini-1.5-pro"
  temperature: 0.7

search:
  provider: "exa"  # or "google" or "crewai"
  max_results: 10

article:
  media_type: "research_magazine"
  length: "medium"
  include_sources: true
  fact_check: false

output:
  directory: "./outputs"
  filename_template: "{date}_{topic}_{media_type}.md"
```

**Most users only need to set:**
- `llm.provider` and `search.provider` (match your API keys)
- `article.media_type` (or override with `--media-type`)

Everything else works with defaults!

## Key Features

- **4-Agent Pipeline**: Research → Write → Edit → Humanize for quality articles
- **Multiple Styles**: 4 publication types with authentic tones
- **Research Integration**: Automatic web search and source citation
- **Context Support**: Provide details about your innovation for better articles
- **Clean Output**: Professional markdown, ready to publish
- **Flexible**: Multiple LLM and search providers supported
- **Humanization**: Advanced techniques to make articles sound natural and human-written

## Troubleshooting

### "Missing API keys" error
- Check `.env` file exists and has correct key names
- Verify keys are valid (test them on provider websites)
- Ensure you have the right keys for your chosen providers

### "Config error"
- Make sure `config.yaml` exists (copy from `config.yaml.example`)
- Check YAML syntax (no tabs, proper indentation)
- Verify `media_type` matches: `scientific_journal`, `research_magazine`, `tech_news`, or `academic_news`

### "No results found"
- Try a different search provider in `config.yaml`
- Check your search API key is valid
- Verify API quota hasn't been exceeded

### Article quality issues
- Use `--context-file` to provide more details about your innovation
- Try different `media_type` for better style match
- Use `--verbose` to see what's happening
- Adjust `temperature` in config (lower = more focused, higher = more creative)

## How It Works

The system uses a **4-agent pipeline**:

1. **Research Agent**
   - Generates search queries using LLM
   - Performs web searches via your configured provider
   - Synthesizes findings into structured research data
   - Tracks sources for citation

2. **Writer Agent**
   - Loads tone/style guidelines for your media type
   - Generates article sections following the template
   - Applies consistent tone throughout
   - Uses research findings and your context (if provided)

3. **Editor Agent**
   - Reviews article for quality and consistency
   - Ensures tone consistency
   - Improves flow and readability
   - Optionally performs fact-checking

4. **Humanizer Agent**
   - Applies advanced humanization techniques
   - Makes writing sound natural and human-authored
   - Removes AI-like patterns and phrasing
   - Configurable intensity and passes for fine-tuning

5. **Formatter**
   - Converts to clean markdown
   - Adds metadata header
   - Formats sources (deduplicated and cleaned)
   - Saves to file

## Advanced Usage

### Customizing Tones

Edit `src/config/tones.yaml` to modify writing styles for each media type.

### Customizing Templates

Edit `src/config/templates.yaml` to change article structure (sections, order, etc.).

### Adding New Media Types

1. Add tone definition to `src/config/tones.yaml`
2. Add template structure to `src/config/templates.yaml`
3. Use: `--media-type your_new_type`

### Using CrewAI Search

If you want to use CrewAI's enhanced search:
```bash
pip install crewai crewai-tools
```
Then set `search.provider: "crewai"` in `config.yaml`.

## Project Structure

```
media-article-writer/
├── src/
│   ├── agents/           # Research, Writer, Editor, Humanizer agents
│   │   ├── research_agent.py
│   │   ├── writer_agent.py
│   │   ├── editor_agent.py
│   │   ├── humanizer_agent.py
│   │   └── crewai_research_agent.py
│   ├── config/           # Tones and templates
│   │   ├── tones.yaml
│   │   └── templates.yaml
│   ├── utils/            # Helpers (LLM, search, formatting)
│   │   ├── llm.py
│   │   ├── search.py
│   │   ├── formatter.py
│   │   ├── env.py
│   │   └── ...
│   ├── pipeline.py        # Main orchestrator
│   └── main.py           # CLI entry point
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test fixtures
├── outputs/              # Generated articles (gitignored)
├── config.yaml.example   # Configuration template
├── config.yaml           # Your configuration (gitignored)
├── .env.example          # Environment variables template
├── .env                  # Your API keys (gitignored)
├── pyproject.toml        # Project metadata and dependencies
├── requirements.txt      # Alternative dependency list
└── README.md             # This file
```

## FAQ

**Q: How long does it take to generate an article?**  
A: Typically 1-3 minutes depending on search results and article length.

**Q: Can I edit the generated article?**  
A: Yes! Articles are saved as markdown files you can edit in any text editor.

**Q: Are sources automatically cited?**  
A: Yes, sources are automatically found, deduplicated, cleaned, and formatted.

**Q: Can I use my own LLM/search provider?**  
A: Currently supports Gemini, Perplexity (LLM) and Exa, Google, CrewAI (search). Adding new providers requires code changes.

**Q: How do I improve article quality?**  
A: Use `--context-file` to provide detailed information about your innovation. The more context, the better the article.

**Q: Can I generate multiple articles at once?**  
A: Run the command multiple times with different topics. Each generates a separate file.

**Q: What is the Humanizer agent?**  
A: The Humanizer agent applies advanced techniques to make AI-generated text sound more natural and human-written. It can be configured via `config.yaml` with intensity levels (low/medium/high) and number of passes (1-3).

## Testing

Run the test suite to verify everything works:

```bash
# Install test dependencies
uv sync --extra test

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_env.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/media-assistant.git
cd media-assistant

# Install dependencies
uv sync --extra test

# Run tests
uv run pytest

# Make your changes and test them
```

## License

This project is licensed under the MIT License - see the LICENSE file for details (or check the repository).

---

**Repository**: [https://github.com/parthchandak02/media-assistant](https://github.com/parthchandak02/media-assistant)
