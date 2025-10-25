# AutoAudit - Auto Dealership Compliance Checker

An AI-powered compliance checker for auto dealership websites that analyzes web content for regulatory compliance with state-specific advertising and disclosure requirements.

## Features

- **Automated Web Scraping**: Uses Playwright to render JavaScript-heavy dealership websites
- **Intelligent Content Extraction**: Converts HTML to clean Markdown for better LLM processing
- **AI-Powered Analysis**: Leverages OpenAI's GPT models to identify compliance violations
- **Multi-State Support**: Pre-configured rules for California, Texas, and New York (easily extensible)
- **Comprehensive Reports**: Generates detailed reports in Markdown, JSON, and HTML formats
- **Batch Processing**: Check multiple dealership websites in a single run

## Architecture

```
URL → Playwright Scraper → HTML-to-Markdown → LLM Analysis → Compliance Report
```

1. **Scraper** (`scraper.py`): Renders JavaScript and extracts HTML content
2. **Converter** (`converter.py`): Cleans HTML and converts to structured Markdown
3. **Analyzer** (`analyzer.py`): Uses OpenAI API to analyze content against state rules
4. **Reporter** (`reporter.py`): Generates formatted compliance reports
5. **Main** (`main.py`): Orchestrates the entire pipeline

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key
- pip (Python package manager)

### Setup

1. Clone or download this repository:
```bash
cd autoaudit
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

5. Set up your OpenAI API key:
```bash
# Create .env file
cp .env.example .env

# Edit .env and add your API key:
# OPENAI_API_KEY=sk-...
```

## Usage

### Basic Usage

Check a single dealership website:

```bash
python main.py https://example-dealership.com --state CA
```

### Check Multiple URLs

```bash
python main.py \
  https://dealership1.com \
  https://dealership2.com \
  https://dealership3.com \
  --state TX
```

### Check Oklahoma Dealership (Comprehensive Rules)

```bash
python main.py https://oklahoma-dealer.com --state OK
```

### Generate Multiple Report Formats

```bash
python main.py https://example-dealership.com \
  --state NY \
  --formats markdown json html
```

### Custom Output Directory

```bash
python main.py https://example-dealership.com \
  --state CA \
  --output ./my-reports
```

### Command-Line Options

```
usage: main.py [-h] -s {CA,TX,NY,OK} [-f {markdown,json,html} [{markdown,json,html} ...]]
               [-o OUTPUT] [--verbose]
               urls [urls ...]

positional arguments:
  urls                  One or more dealership website URLs to check

options:
  -h, --help            Show this help message and exit
  -s, --state {CA,TX,NY,OK}
                        State code for compliance rules (e.g., CA, TX, NY, OK)
  -f, --formats {markdown,json,html}
                        Report formats to generate (default: markdown)
  -o, --output OUTPUT   Output directory for reports (default: reports)
  --verbose             Enable verbose logging
```

## Configuration

### Adding New States

Edit `config.py` to add new state regulations:

```python
STATE_REGULATIONS["FL"] = StateRules(
    state="Florida",
    required_disclosures=[
        "Your disclosure requirements here",
    ],
    pricing_rules=[
        "Pricing rules here",
    ],
    financing_rules=[
        "Financing rules here",
    ],
)
```

### Adjusting LLM Settings

In `config.py`, you can modify:

```python
OPENAI_MODEL = "gpt-4o-mini"  # or "gpt-4o" for better accuracy
MAX_TOKENS = 4000
TEMPERATURE = 0.1  # Lower = more consistent
```

## Project Structure

```
autoaudit/
├── main.py              # Main orchestration script
├── scraper.py           # Playwright-based web scraper
├── converter.py         # HTML to Markdown converter
├── analyzer.py          # LLM compliance analyzer
├── reporter.py          # Report generator
├── config.py            # Configuration and state rules
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── reports/            # Generated reports (created automatically)
```

## Example Output

After running a compliance check, you'll see output like:

```
✅ Compliance Check Results
============================================================
URL: https://example-dealership.com
State: California
Status: NEEDS_REVIEW
Score: 65/100

Summary: The website has several compliance issues primarily
related to incomplete pricing disclosures and missing
financing terms.

⚠️  3 violation(s) found:
  1. [HIGH] Advertised price must include all dealer-imposed fees
  2. [MEDIUM] APR must be disclosed if financing terms mentioned
  3. [LOW] Documentary fee limits and disclosure

Reports saved:
  markdown: reports/compliance_report_example-dealership.com_20241024_143022.md
============================================================
```

## Sample Report Structure

Generated reports include:

- **Overall Compliance Status**: Score and summary
- **Violations Found**: Detailed list with severity, evidence, and recommendations
- **Compliant Items**: What the site is doing correctly
- **Missing Information**: Required disclosures not found
- **Recommendations**: Actionable steps to improve compliance

## State Compliance Rules

### Currently Supported States

- **California (CA)**: Vehicle history, smog certification, lemon law, pricing transparency
- **Texas (TX)**: Inventory tax, title status, odometer disclosure, documentary fees
- **New York (NY)**: Lemon law, warranty information, interest rate disclosure
- **Oklahoma (OK)**: Comprehensive rules based on OAC 465:15 including:
  - Required vehicle identification adjacent to price
  - Stock number or quantity disclosure requirements
  - Prior service disclosure (demonstrator, loaner, etc.)
  - Prohibited terminology ("invoice", "dealer cost", "guaranteed approval", etc.)
  - Strict pricing transparency (no "with trade" qualifiers)
  - Savings claims only from MSRP
  - Detailed lease disclosure requirements
  - FTC Regulation M and Z compliance

### Extending to More States

1. Research state-specific regulations
2. Add rules to `config.py`
3. Update README with new state details

## Technical Details

### Why Python Over Node.js?

For this use case, Python offers:
- Superior HTML-to-Markdown conversion libraries
- More mature LLM orchestration frameworks
- Better document processing ecosystem
- Robust async support for concurrent scraping

### Performance Considerations

- **Concurrent scraping**: The scraper can process multiple URLs in parallel
- **Token optimization**: Content is intelligently truncated to stay within LLM limits
- **Caching**: Consider implementing prompt caching for state rules (OpenAI feature)
- **Rate limiting**: Add delays if checking many URLs to avoid rate limits

### Future Enhancements

- [ ] Add support for more states
- [ ] Implement prompt caching for better performance
- [ ] Add support for GPT-5 when available
- [ ] Create web dashboard for results visualization
- [ ] Add database storage for historical tracking
- [ ] Implement screenshot capture for visual evidence
- [ ] Add PDF report generation
- [ ] Support for dealership platform-specific extraction
- [ ] Automated scheduling and monitoring

## Troubleshooting

### Common Issues

**Playwright installation fails:**
```bash
# Try installing browsers manually
python -m playwright install chromium
```

**OpenAI API errors:**
- Verify your API key is correct in `.env`
- Check your OpenAI account has available credits
- Ensure you have access to the specified model

**Scraping timeout errors:**
- Increase `SCRAPING_TIMEOUT` in `config.py`
- Check if the website has anti-bot protection
- Try running with `--verbose` flag for more details

**Module not found errors:**
```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -r requirements.txt
```

## Legal Disclaimer

This tool is designed to assist with compliance checking but should not be considered legal advice. All findings should be reviewed by qualified legal counsel before taking action. Compliance rules vary by jurisdiction and change over time.

## Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Add your changes with tests
4. Submit a pull request

## License

[Add your license here]

## Support

For issues, questions, or feature requests, please open an issue on the project repository.

## Acknowledgments

- Built with OpenAI's GPT models
- Uses Playwright for browser automation
- html2text for content conversion
