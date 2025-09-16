"""
CloudPinokio Streamlit Web Interface
A modern web UI for browsing, installing, and managing Pinokio apps in cloud environments
"""

import streamlit as st
import asyncio
import pandas as pd
import time
from typing import Dict, Any, List
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import existing components instead of creating new ones
try:
    from pinokios.database import PINOKIO_APPS, search_apps, get_stats
    from pinokios.engine import PinokioEngine
    from pinokio_app_manager import PinokioAppManager
    from pinokio_emulator import PinokioEmulator
    CLOUD_MODE = True
    print("✅ Using existing Pinokio components with cloud enhancements")
except ImportError as e:
    print(f"⚠️ Could not import existing components: {e}")
    CLOUD_MODE = False

# Page configuration
st.set_page_config(
    page_title="CloudPinokio - AI App Store for Cloud",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .app-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    
    .category-badge {
        background: #667eea;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    
    .status-installed {
        color: #28a745;
        font-weight: bold;
    }
    
    .status-installing {
        color: #ffc107;
        font-weight: bold;
    }
    
    .status-failed {
        color: #dc3545;
        font-weight: bold;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Cloud-Enhanced Pinokio Engine
@st.cache_resource
def init_engine():
    """Initialize cloud-enhanced Pinokio engine (cached for performance)"""
    try:
        if CLOUD_MODE:
            # Use existing Pinokio engine with cloud enhancements
            engine = PinokioEngine()
            # Add cloud capabilities
            engine.app_manager = PinokioAppManager()
            engine.emulator = PinokioEmulator()
            print(f"✅ Initialized cloud-enhanced Pinokio with {len(PINOKIO_APPS)} apps")
            return engine
        else:
            st.error("Could not initialize Pinokio components")
            return None
    except Exception as e:
        st.error(f"Failed to initialize Pinokio engine: {e}")
        return None

def detect_cloud_environment():
    """Detect current cloud environment"""
    if 'google.colab' in sys.modules:
        return 'Google Colab'
    elif os.environ.get('LIGHTNING_CLOUD_URL'):
        return 'Lightning AI'
    elif 'kaggle_web_client' in sys.modules or os.path.exists('/kaggle'):
        return 'Kaggle'
    else:
        return 'Local/Other'

# Initialize session state
if 'engine' not in st.session_state:
    st.session_state.engine = init_engine()
    
if 'selected_app' not in st.session_state:
    st.session_state.selected_app = None
    
if 'installation_progress' not in st.session_state:
    st.session_state.installation_progress = {}

def main():
    """Main application interface"""
    
    engine = st.session_state.engine
    if not engine:
        st.error("⚠️ CloudPinokio engine failed to initialize. Please check your setup.")
        return
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 CloudPinokio</h1>
        <p>AI App Store for Cloud GPU Environments</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/667eea/ffffff?text=CloudPinokio", use_column_width=True)
        
        page = st.selectbox(
            "Navigate",
            ["🏠 Home", "🔍 Browse Apps", "📦 Installed Apps", "⚙️ System Info"],
            index=0
        )
        
        # System status
        st.markdown("### System Status")
        system_info = engine.get_system_info()
        
        if system_info['gpu_info']['available']:
            st.success(f"🟢 GPU: {system_info['gpu_info']['name']}")
        else:
            st.warning("🟡 No GPU detected")
            
        st.info(f"💾 Memory: {system_info['memory_gb']:.1f} GB")
        st.info(f"🗄️ Storage: {system_info['storage_gb']:.1f} GB")
        st.info(f"🌍 Environment: {system_info['environment'].title()}")
    
    # Main content based on selected page
    if page == "🏠 Home":
        show_home_page(engine)
    elif page == "🔍 Browse Apps":
        show_browse_page(engine)
    elif page == "📦 Installed Apps":
        show_installed_page(engine)
    elif page == "⚙️ System Info":
        show_system_page(engine)

def show_home_page(engine):
    """Show home page with overview and popular apps"""
    
    # Library statistics
    stats = engine.get_library_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{stats['total_apps']}</h2>
            <p>Total Apps</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{len(engine.get_installed_apps())}</h2>
            <p>Installed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{len(stats['categories'])}</h2>
            <p>Categories</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h2>{stats['verified_pinokio_apps']}</h2>
            <p>Verified Apps</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Popular Apps
    st.markdown("## 🔥 Popular Apps")
    popular_apps = engine.get_popular_apps(limit=6)
    
    if popular_apps:
        cols = st.columns(2)
        for i, app in enumerate(popular_apps):
            with cols[i % 2]:
                render_app_card(app, engine, compact=True)
    else:
        st.info("No popular apps available")
    
    # Categories Overview
    st.markdown("## 📂 Categories")
    categories = engine.get_categories()
    
    cols = st.columns(3)
    for i, category in enumerate(categories):
        with cols[i % 3]:
            app_count = len(engine.get_apps_by_category(category))
            st.metric(category, app_count)

def show_browse_page(engine):
    """Show app browsing page with search and filtering"""
    
    st.markdown("## 🔍 Browse Apps")
    
    # Search and filter controls
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search apps", placeholder="Enter app name, description, or tags...")
    
    with col2:
        categories = ["All"] + engine.get_categories()
        selected_category = st.selectbox("Category", categories)
    
    with col3:
        sort_by = st.selectbox("Sort by", ["Popularity", "Name", "Category"])
    
    # Get apps based on search/filter
    if search_query:
        apps = engine.search_apps(
            search_query, 
            category=None if selected_category == "All" else selected_category,
            limit=50
        )
    elif selected_category != "All":
        apps = engine.get_apps_by_category(selected_category)
    else:
        apps = engine.get_popular_apps(limit=50)
    
    # Sort apps
    if sort_by == "Name":
        apps.sort(key=lambda x: x.name.lower())
    elif sort_by == "Category":
        apps.sort(key=lambda x: x.category)
    # Popularity is default sort
    
    st.markdown(f"**Found {len(apps)} apps**")
    
    # Display apps
    if apps:
        for app in apps:
            render_app_card(app, engine)
    else:
        st.info("No apps found matching your criteria.")

def show_installed_page(engine):
    """Show installed apps page"""
    
    st.markdown("## 📦 Installed Apps")
    
    installed_app_ids = engine.get_installed_apps()
    
    if not installed_app_ids:
        st.info("No apps installed yet. Visit the Browse page to install some apps!")
        return
    
    st.markdown(f"**{len(installed_app_ids)} apps installed**")
    
    for app_id in installed_app_ids:
        app = engine.get_app(app_id)
        if app:
            render_installed_app_card(app, engine)

def show_system_page(engine):
    """Show system information page"""
    
    st.markdown("## ⚙️ System Information")
    
    system_info = engine.get_system_info()
    
    # Environment Info
    st.markdown("### Environment")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Platform**: {system_info['environment'].title()}")
        st.info(f"**Python**: {system_info['python_version']}")
        
    with col2:
        st.info(f"**Apps Directory**: {system_info['apps_directory']}")
        if system_info['persistent_storage']:
            st.info(f"**Persistent Storage**: {system_info['persistent_storage']}")
    
    # GPU Info
    st.markdown("### GPU Information")
    if system_info['gpu_info']['available']:
        st.success(f"✅ **GPU Available**: {system_info['gpu_info']['name']}")
        st.success(f"💾 **GPU Memory**: {system_info['gpu_info']['memory_gb']:.1f} GB")
    else:
        st.warning("⚠️ No GPU detected")
    
    # Memory and Storage
    st.markdown("### Resources")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Available RAM", f"{system_info['memory_gb']:.1f} GB")
    
    with col2:
        st.metric("Available Storage", f"{system_info['storage_gb']:.1f} GB")
    
    # Library Stats
    st.markdown("### Library Statistics")
    stats = engine.get_library_stats()
    
    df = pd.DataFrame([
        {"Metric": "Total Apps", "Value": stats['total_apps']},
        {"Metric": "Verified Pinokio Apps", "Value": stats['verified_pinokio_apps']},
        {"Metric": "JS Installers", "Value": stats['js_installers']},
        {"Metric": "JSON Installers", "Value": stats['json_installers']},
    ])
    
    st.dataframe(df, use_container_width=True)
    
    # Category breakdown
    st.markdown("### Categories")
    category_data = []
    for category, count in stats['categories'].items():
        category_data.append({"Category": category, "Apps": count})
    
    if category_data:
        df_categories = pd.DataFrame(category_data)
        st.bar_chart(df_categories.set_index('Category'))

def render_app_card(app, engine, compact=False):
    """Render an app card"""
    
    is_installed = engine.is_app_installed(app.id)
    installation_status = engine.get_installation_status(app.id)
    
    # Status indicator
    if is_installed:
        status_html = '<span class="status-installed">✅ Installed</span>'
    elif installation_status and installation_status.status == 'installing':
        status_html = '<span class="status-installing">🔄 Installing...</span>'
    elif installation_status and installation_status.status == 'failed':
        status_html = '<span class="status-failed">❌ Failed</span>'
    else:
        status_html = ''
    
    # App card HTML
    card_html = f"""
    <div class="app-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="flex: 1;">
                <h3 style="margin: 0 0 0.5rem 0; color: #333;">{app.name}</h3>
                <p style="margin: 0 0 1rem 0; color: #666; font-size: 0.9rem;">
                    {app.description[:200]}{'...' if len(app.description) > 200 else ''}
                </p>
                <div style="margin-bottom: 1rem;">
                    <span class="category-badge">{app.category}</span>
                    <small style="color: #888;">⭐ {app.stars} | 👤 {app.author}</small>
                </div>
                {status_html}
            </div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if st.button("📖 Details", key=f"details_{app.id}"):
            show_app_details(app, engine)
    
    with col2:
        if is_installed:
            if st.button("🚀 Launch", key=f"launch_{app.id}"):
                launch_app(app, engine)
        else:
            disabled = installation_status and installation_status.status == 'installing'
            if st.button("📥 Install", key=f"install_{app.id}", disabled=disabled):
                install_app(app, engine)
    
    with col3:
        if is_installed and st.button("🗑️ Remove", key=f"remove_{app.id}"):
            if st.confirm(f"Remove {app.name}?"):
                remove_app(app, engine)
    
    with col4:
        if st.button("🔗 GitHub", key=f"github_{app.id}"):
            st.markdown(f"[Open GitHub Repository]({app.repo_url})")

def render_installed_app_card(app, engine):
    """Render an installed app card with launch options"""
    
    st.markdown(f"""
    <div class="app-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: #333;">{app.name}</h3>
                <span class="category-badge">{app.category}</span>
                <span class="status-installed">✅ Installed</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 Launch", key=f"launch_installed_{app.id}"):
            launch_app(app, engine)
    
    with col2:
        if st.button("🗑️ Remove", key=f"remove_installed_{app.id}"):
            if st.confirm(f"Remove {app.name}?"):
                remove_app(app, engine)

def show_app_details(app, engine):
    """Show detailed app information in a modal"""
    
    st.modal("App Details")
    
    with st.container():
        st.markdown(f"# {app.name}")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Description**: {app.description}")
            st.markdown(f"**Author**: {app.author}")
            st.markdown(f"**Category**: {app.category}")
            st.markdown(f"**Stars**: ⭐ {app.stars}")
            
            if app.tags:
                st.markdown(f"**Tags**: {', '.join(app.tags)}")
        
        with col2:
            st.markdown(f"**Installer Type**: {app.installer_type}")
            st.markdown(f"**Has install.js**: {'✅' if app.has_install_js else '❌'}")
            st.markdown(f"**Has install.json**: {'✅' if app.has_install_json else '❌'}")
            st.markdown(f"**Has pinokio.js**: {'✅' if app.has_pinokio_js else '❌'}")
        
        st.markdown(f"**Repository**: [{app.repo_url}]({app.repo_url})")

def install_app(app, engine):
    """Install an app with progress tracking"""
    
    progress_container = st.empty()
    status_container = st.empty()
    
    with progress_container.container():
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    def progress_callback(app_id, progress, message):
        progress_bar.progress(progress / 100)
        status_text.text(message)
    
    engine.add_progress_callback(progress_callback)
    
    # Run installation in async context
    async def run_install():
        return await engine.install_app(app.id)
    
    try:
        # Run async installation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_install())
        loop.close()
        
        if result.status == 'installed':
            status_container.success(f"✅ {app.name} installed successfully!")
        else:
            status_container.error(f"❌ Installation failed: {result.error}")
            
    except Exception as e:
        status_container.error(f"❌ Installation error: {str(e)}")
    
    progress_container.empty()

def launch_app(app, engine):
    """Launch an installed app"""
    
    with st.spinner(f"Launching {app.name}..."):
        async def run_launch():
            return await engine.launch_app(app.id)
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(run_launch())
            loop.close()
            
            if result['success']:
                st.success(f"🚀 {app.name} launched successfully!")
                # Could show output in expander
                with st.expander("Launch Output"):
                    for r in result['results']:
                        if r['output']:
                            st.code(r['output'])
            else:
                st.error(f"❌ Launch failed: {result['error']}")
                
        except Exception as e:
            st.error(f"❌ Launch error: {str(e)}")

def remove_app(app, engine):
    """Remove an installed app"""
    
    with st.spinner(f"Removing {app.name}..."):
        success = engine.uninstall_app(app.id)
        
        if success:
            st.success(f"🗑️ {app.name} removed successfully!")
            st.experimental_rerun()
        else:
            st.error(f"❌ Failed to remove {app.name}")

if __name__ == "__main__":
    main()
