# 📚 Leopold's Research Digest

A personalized research monitoring system that automatically:
- Crawls academic repositories (arXiv, OpenAlex, NBER) daily
- Filters papers relevant to your research interests
- **Validates all papers are real** (DOI verification - no hallucinated papers!)
- Generates AI summaries using Claude
- Sends beautiful email digests
- Provides a web dashboard for browsing

## 🎯 Research Focus

This system is configured for research in:
- **Market Design** (mechanism design, auction theory, capacity markets)
- **Energy Economics** (electricity markets, power markets, pricing)
- **Environmental Economics** (carbon pricing, emissions trading, renewable integration)
- **Industrial Organization** (vertical integration, regulation)

## 🚀 Quick Start

### 1. Clone and Install

```bash
# Clone the repo
git clone https://github.com/LeopoldM/research-digest.git
cd research-digest

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file (or set environment variables):

```bash
# Required for AI summaries
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Required for email delivery
SENDGRID_API_KEY=SG.xxxxx
SENDGRID_FROM_EMAIL=your-verified-sender@example.com

# Your email address
DIGEST_EMAIL=leopold.monjoie@aalto.fi
```

**Getting API Keys:**
- **Anthropic Claude**: Sign up at [console.anthropic.com](https://console.anthropic.com) (free credits available)
- **SendGrid**: Sign up at [sendgrid.com](https://sendgrid.com) (100 free emails/day)

### 3. Run Locally

```bash
# Run daily digest
python run_digest.py --daily

# Run weekly digest
python run_digest.py --weekly
```

### 4. View Dashboard

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 in your browser.

## 📧 Email Setup (SendGrid)

1. Create a SendGrid account at https://sendgrid.com
2. Verify a sender email address
3. Create an API key with "Mail Send" permissions
4. Add the API key to your environment variables

## ⚙️ GitHub Actions (Automated Daily Runs)

To run automatically:

1. Push this repo to GitHub
2. Go to **Settings > Secrets and variables > Actions**
3. Add these secrets:
   - `ANTHROPIC_API_KEY`
   - `SENDGRID_API_KEY`
   - `SENDGRID_FROM_EMAIL`
   - `DIGEST_EMAIL`
4. Enable Actions in your repo

The digest will run:
- **Daily** at 6:00 AM Helsinki time
- **Weekly** on Sundays at 8:00 AM Helsinki time

## 🌐 Deploy Dashboard (Streamlit Cloud)

Free hosting for the web dashboard:

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `dashboard/app.py` as the main file
5. Deploy!

## 📁 Project Structure

```
research-digest/
├── run_digest.py           # Main script
├── requirements.txt        
├── .env                    # Your API keys (don't commit!)
├── config/
│   ├── keywords.yaml       # Your research keywords
│   └── sources.yaml        # Data sources config
├── src/
│   ├── collectors/         # Paper fetchers
│   │   ├── arxiv_collector.py
│   │   ├── openalex_collector.py
│   │   └── nber_collector.py
│   ├── processors/         # Paper processing
│   │   ├── doi_validator.py    # ⚠️ Prevents fake papers!
│   │   ├── relevance_scorer.py
│   │   └── summarizer.py
│   └── outputs/            # Formatting & sending
│       ├── digest_formatter.py
│       └── email_sender.py
├── dashboard/
│   └── app.py              # Streamlit dashboard
├── data/                   # Generated digests (JSON/HTML)
└── .github/workflows/      # Automated runs
```

## 🔧 Customization

### Change Keywords

Edit `config/keywords.yaml` to adjust research interests:

```yaml
primary_keywords:
  your_topic:
    - "keyword 1"
    - "keyword 2"
```

### Add Data Sources

Add new collectors in `src/collectors/` following the same pattern.

### Adjust Scoring

Modify weights in `src/processors/relevance_scorer.py`.

## ⚠️ Important: DOI Validation

This system validates every paper before inclusion to avoid the "hallucination" problem where AI might suggest fake papers. See `src/processors/doi_validator.py`.

## 📄 License

MIT License - feel free to adapt for your own research!

## 🙏 Credits

Inspired by Alex Imas's tweet about his research digest system, and Eugen Dimant's one-shot replication experiment.
