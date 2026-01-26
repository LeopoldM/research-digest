"""
Research Digest Dashboard

A Streamlit web interface to browse your research digest.
Run locally: streamlit run dashboard/app.py
Deploy free: https://streamlit.io/cloud
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="Leopold's Research Digest",
    page_icon="📚",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .paper-card {
        border-left: 4px solid #2563eb;
        padding-left: 15px;
        margin: 15px 0;
        background: #f8fafc;
        padding: 15px;
        border-radius: 0 8px 8px 0;
    }
    .score-high { color: #059669; font-weight: bold; }
    .score-medium { color: #d97706; font-weight: bold; }
    .score-low { color: #6b7280; }
    .source-badge {
        background: #e5e7eb;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }
    .timestamp-box {
        background: #dbeafe;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 10px 15px;
        margin: 10px 0;
    }
    .last-updated {
        color: #1e40af;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def load_digests():
    """Load all digest files"""
    data_dir = Path(__file__).parent.parent / "data"
    
    digests = []
    if data_dir.exists():
        for file in sorted(data_dir.glob("*.json"), reverse=True):
            try:
                with open(file) as f:
                    data = json.load(f)
                    data['filename'] = file.name
                    digests.append(data)
            except:
                continue
    
    return digests


def format_timestamp(iso_timestamp):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime("%A, %B %d, %Y at %H:%M:%S UTC")
    except:
        return iso_timestamp


def format_timestamp_short(iso_timestamp):
    """Format ISO timestamp to short format"""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_timestamp


def format_score(score):
    """Format relevance score with color"""
    if score >= 50:
        return f'<span class="score-high">🔥 {score:.0f}</span>'
    elif score >= 25:
        return f'<span class="score-medium">📌 {score:.0f}</span>'
    else:
        return f'<span class="score-low">{score:.0f}</span>'


def main():
    st.title("📚 Leopold's Research Digest")
    st.markdown("*Personalized academic paper recommendations*")
    
    # Load digests once
    digests = load_digests()
    
    # Show last update time prominently at the top
    if digests:
        latest = digests[0]
        generated_at = latest.get('generated_at', 'Unknown')
        st.markdown(f"""
        <div class="timestamp-box">
            🕐 <span class="last-updated">Last Updated:</span> {format_timestamp(generated_at)}
        </div>
        """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Filter options
        min_score = st.slider("Minimum relevance score", 0, 100, 10)
        
        sources = st.multiselect(
            "Sources",
            ["arxiv", "openalex", "nber"],
            default=["arxiv", "openalex", "nber"]
        )
        
        st.divider()
        
        # Quick stats
        if digests:
            total_papers = sum(d.get('paper_count', 0) for d in digests)
            st.metric("Total Papers Collected", total_papers)
            st.metric("Digests Available", len(digests))
            
            st.divider()
            
            # Show all digest timestamps
            st.subheader("📅 Digest History")
            for d in digests[:10]:  # Show last 10
                timestamp = format_timestamp_short(d.get('generated_at', 'Unknown'))
                period = d.get('period', 'daily').capitalize()
                count = d.get('paper_count', 0)
                st.markdown(f"• **{timestamp}** - {period} ({count} papers)")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📅 Latest Digest", "📊 Browse All", "⭐ Reading List"])
    
    with tab1:
        st.header("Latest Digest")
        
        if not digests:
            st.info("No digests found yet. Run the digest script first!")
            st.code("python run_digest.py --daily", language="bash")
        else:
            latest = digests[0]
            
            # Show generation info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📅 Generated", format_timestamp_short(latest.get('generated_at', 'Unknown')))
            with col2:
                st.metric("📄 Papers Found", latest.get('paper_count', 0))
            with col3:
                st.metric("📋 Type", latest.get('period', 'daily').capitalize())
            
            st.divider()
            
            papers = latest.get('papers', [])
            
            # Filter papers
            filtered_papers = [
                p for p in papers 
                if p.get('relevance_score', 0) >= min_score
                and p.get('source', '') in sources
            ]
            
            st.markdown(f"*Showing {len(filtered_papers)} of {len(papers)} papers*")
            
            for paper in filtered_papers:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"### [{paper['title']}]({paper['url']})")
                        
                        # Metadata
                        authors = ", ".join(paper.get('authors', [])[:3])
                        if len(paper.get('authors', [])) > 3:
                            authors += " et al."
                        
                        st.markdown(f"""
                        <span class="source-badge">{paper.get('source', 'unknown').upper()}</span>
                        {' • ' + authors if authors else ''}
                        {' • ' + paper.get('published_date', '') if paper.get('published_date') else ''}
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        score = paper.get('relevance_score', 0)
                        st.markdown(f"**Score:** {format_score(score)}", unsafe_allow_html=True)
                    
                    # Summary or abstract
                    if paper.get('summary'):
                        st.markdown(f"*{paper['summary']}*")
                    elif paper.get('abstract'):
                        with st.expander("Abstract"):
                            st.write(paper['abstract'][:500] + "..." if len(paper.get('abstract', '')) > 500 else paper.get('abstract', ''))
                    
                    st.divider()
    
    with tab2:
        st.header("Browse All Digests")
        
        if not digests:
            st.info("No digests available yet.")
        else:
            # Digest selector with timestamps
            digest_options = {
                f"{format_timestamp_short(d.get('generated_at', 'Unknown'))} - {d.get('period', 'daily')} ({d.get('paper_count', 0)} papers)": i
                for i, d in enumerate(digests)
            }
            
            selected = st.selectbox("Select digest", list(digest_options.keys()))
            
            if selected:
                idx = digest_options[selected]
                digest = digests[idx]
                
                # Show selected digest info
                st.markdown(f"""
                <div class="timestamp-box">
                    🕐 <span class="last-updated">Generated:</span> {format_timestamp(digest.get('generated_at', 'Unknown'))}
                </div>
                """, unsafe_allow_html=True)
                
                papers = digest.get('papers', [])
                
                # Show as table
                if papers:
                    import pandas as pd
                    
                    df = pd.DataFrame([
                        {
                            'Title': p.get('title', '')[:80] + '...' if len(p.get('title', '')) > 80 else p.get('title', ''),
                            'Source': p.get('source', ''),
                            'Score': p.get('relevance_score', 0),
                            'Date': p.get('published_date', ''),
                            'URL': p.get('url', '')
                        }
                        for p in papers
                    ])
                    
                    st.dataframe(
                        df,
                        column_config={
                            "URL": st.column_config.LinkColumn("URL"),
                            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100)
                        },
                        hide_index=True
                    )
    
    with tab3:
        st.header("⭐ Reading List")
        st.info("Coming soon! Save papers to your reading list for later.")
        
        # Placeholder for reading list functionality
        st.markdown("""
        Future features:
        - Save papers to reading list
        - Mark as read/unread
        - Add notes
        - Export to reference manager
        """)


if __name__ == "__main__":
    main()
