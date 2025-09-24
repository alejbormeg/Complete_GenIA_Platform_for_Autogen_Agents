# src/starlite_app/__init__.py
from pathlib import Path

# IMPORTANT: we are on starlite==1.x, not "litestar"
from starlite import Starlite, get, TemplateConfig
from starlite.response import Template
from starlite.contrib.jinja import Jinja2Engine

# If you serve static assets, you can enable StaticFilesConfig as shown below
try:
    from starlite.config.static_files import StaticFilesConfig
except Exception:
    StaticFilesConfig = None  # starlite is present; this is defensive

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

template_config = TemplateConfig(directory=TEMPLATES_DIR, engine=Jinja2Engine)

@get("/")
def index() -> Template:
    # Render your Jinja template. Make sure templates/index.html exists
    return Template(name="index.html", context={"title": "App"})

static_files = None
if StaticFilesConfig and STATIC_DIR.exists():
    static_files = [StaticFilesConfig(path="/static", directories=[STATIC_DIR])]

app = Starlite(
    route_handlers=[index],
    template_config=template_config,
    static_files_config=static_files or [],
)
