#!/usr/bin/env python3
"""
Build script for course syllabi.

Reads course configuration from YAML files, Google Sheets, or cached JSON
and generates static HTML pages using Jinja2 templates.

Usage:
    python build.py                    # Build all courses from YAML
    python build.py sp26/math140b      # Build specific course
    python build.py --clean            # Clean output directory first
    python build.py --from-sheets      # Fetch config from Google Sheets
    python build.py --from-sheets --save-cache  # Fetch and save to JSON cache
    python build.py --from-cache       # Build from cached JSON (no API calls)
    python build.py --pdf              # Also generate PDF versions of pages

Environment variables (for --from-sheets):
    GOOGLE_SERVICE_ACCOUNT_FILE - Path to service account JSON
    MATH140B_COURSE_CONFIG_ID   - Sheet ID for Math 140B config
    MATH141B_COURSE_CONFIG_ID   - Sheet ID for Math 141B config
    SEMESTER_NAME               - Term name (e.g., "Spring 2026")
"""

import argparse
import json
import os
import re
import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on system environment variables


# Project paths
PROJECT_ROOT = Path(__file__).parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "docs"
STATIC_DIR = PROJECT_ROOT / "static"


def load_config(config_path: Path) -> dict:
    """Load course configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_config_from_sheets(course: str) -> dict:
    """Load course configuration from Google Sheets.

    Args:
        course: Course identifier (e.g., "math140b")

    Returns:
        Configuration dictionary matching YAML structure
    """
    from sheets_fetcher import fetch_config_from_sheets

    # Map course to environment variable name
    course_upper = course.upper().replace("-", "")
    sheet_id_var = f"{course_upper}_COURSE_CONFIG_ID"
    sheet_id = os.environ.get(sheet_id_var)

    if not sheet_id:
        raise ValueError(
            f"Environment variable {sheet_id_var} not set. "
            f"Set it to the Google Sheets ID for {course} configuration."
        )

    return fetch_config_from_sheets(course, sheet_id)


def save_config_to_cache(term: str, course: str, config: dict):
    """Save configuration to JSON cache file.

    Args:
        term: Term directory name (e.g., "sp26")
        course: Course name (e.g., "math140b")
        config: Configuration dictionary to cache
    """
    cache_dir = DATA_DIR / term
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{course}.json"

    with open(cache_file, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  Cached: {cache_file.relative_to(PROJECT_ROOT)}")


def load_config_from_cache(term: str, course: str) -> dict:
    """Load configuration from JSON cache file.

    Args:
        term: Term directory name (e.g., "sp26")
        course: Course name (e.g., "math140b")

    Returns:
        Configuration dictionary from cache
    """
    cache_file = DATA_DIR / term / f"{course}.json"
    if not cache_file.exists():
        raise FileNotFoundError(f"Cache file not found: {cache_file}")

    with open(cache_file, "r") as f:
        return json.load(f)


def get_cached_courses() -> list[tuple[str, str]]:
    """Find all courses with cached JSON files.

    Returns list of (term, course) tuples.
    """
    courses = []
    if not DATA_DIR.exists():
        return courses
    for term_dir in DATA_DIR.iterdir():
        if term_dir.is_dir() and not term_dir.name.startswith("."):
            for cache_file in term_dir.glob("*.json"):
                courses.append((term_dir.name, cache_file.stem))
    return sorted(courses)


def get_sheets_courses() -> list[tuple[str, str]]:
    """Find courses configured via environment variables for Sheets mode.

    Returns list of (term, course) tuples based on available sheet IDs.
    """
    courses = []
    term = os.environ.get("SEMESTER_NAME", "Spring 2026")

    # Convert term to directory format (e.g., "Spring 2026" -> "sp26")
    term_parts = term.lower().split()
    if len(term_parts) >= 2:
        season = term_parts[0][:2]  # "sp" or "fa"
        year = term_parts[-1][-2:]  # "26"
        term_dir = f"{season}{year}"
    else:
        term_dir = "sp26"  # Default

    # Check for configured courses
    course_patterns = [
        ("math140b", "MATH140B_COURSE_CONFIG_ID"),
        ("math141b", "MATH141B_COURSE_CONFIG_ID"),
        ("math198", "MATH198_COURSE_CONFIG_ID"),
    ]

    for course, env_var in course_patterns:
        if os.environ.get(env_var):
            courses.append((term_dir, course))

    return courses


def get_all_courses() -> list[tuple[str, str]]:
    """Find all course configs in data directory.

    Returns list of (term, course) tuples, e.g. [('sp26', 'math140b')]
    """
    courses = []
    for term_dir in DATA_DIR.iterdir():
        if term_dir.is_dir() and not term_dir.name.startswith("."):
            for config_file in term_dir.glob("*.yaml"):
                courses.append((term_dir.name, config_file.stem))
    return sorted(courses)


def setup_jinja_env() -> Environment:
    """Create and configure Jinja2 environment."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def copy_static_files(output_path: Path, config: dict):
    """Copy static files (CSS, JS) to output directory.

    Customizes navigation.js with course-specific data.
    """
    static_output = output_path / "static"
    if static_output.exists():
        shutil.rmtree(static_output)
    shutil.copytree(STATIC_DIR, static_output)

    # Customize navigation.js with course-specific data
    nav_js_path = static_output / "navigation.js"
    if nav_js_path.exists():
        nav_js = nav_js_path.read_text()

        # Replace Course Hub URL placeholder
        course_hub_url = config.get("course", {}).get("course_hub_url", "#")
        nav_js = nav_js.replace("#COURSE_HUB_URL#", course_hub_url)

        # Build important dates from config
        important_dates = config.get("important_dates", {})
        exams = config.get("exams", {})

        dates_list = []
        if important_dates.get("regular_drop"):
            dates_list.append(f"Regular Drop Deadline: {important_dates['regular_drop']}")
        if exams.get("midterm1", {}).get("display"):
            dates_list.append(f"Midterm One: {exams['midterm1']['display']}")
        if exams.get("midterm2", {}).get("display"):
            dates_list.append(f"Midterm Two: {exams['midterm2']['display']}")
        # Add make-up quiz sessions
        for session in exams.get("makeup_quiz_sessions", []):
            if session.get("date"):
                dates_list.append(f"Make-up Quiz Session: {session['date']}")
        if important_dates.get("late_drop"):
            dates_list.append(f"Late Drop: {important_dates['late_drop']}")
        if important_dates.get("finals_week"):
            dates_list.append(f"Finals Week: {important_dates['finals_week']}")

        # Replace importantDates array in navigation.js
        if dates_list:
            dates_js = ",\n        ".join(f'"{d}"' for d in dates_list)
            # Use regex to replace the importantDates array
            pattern = r'importantDates:\s*\[[\s\S]*?\]'
            replacement = f'importantDates: [\n        {dates_js}\n    ]'
            nav_js = re.sub(pattern, replacement, nav_js)

        nav_js_path.write_text(nav_js)


def build_course(env: Environment, term: str, course: str, from_sheets: bool = False,
                  from_cache: bool = False, save_cache: bool = False,
                  generate_pdf: bool = False):
    """Build all pages for a single course.

    Args:
        env: Jinja2 environment
        term: Term directory name (e.g., "sp26")
        course: Course name (e.g., "math140b")
        from_sheets: If True, fetch config from Google Sheets
        from_cache: If True, load config from JSON cache
        save_cache: If True, save fetched config to JSON cache
        generate_pdf: If True, also generate PDF versions of pages
    """
    if from_cache:
        try:
            config = load_config_from_cache(term, course)
        except Exception as e:
            print(f"Error loading config from cache: {e}")
            return False
    elif from_sheets:
        try:
            config = load_config_from_sheets(course)
            if save_cache:
                save_config_to_cache(term, course, config)
        except Exception as e:
            print(f"Error loading config from sheets: {e}")
            return False
    else:
        config_path = DATA_DIR / term / f"{course}.yaml"
        if not config_path.exists():
            print(f"Error: Config not found: {config_path}")
            return False
        config = load_config(config_path)

    output_path = OUTPUT_DIR / term / course

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Copy static files (with course-specific customization)
    copy_static_files(output_path, config)

    # Build each page template
    pages_dir = TEMPLATES_DIR / "pages"
    if not pages_dir.exists():
        print(f"Warning: No pages directory found at {pages_dir}")
        return True

    # Define page order for combined PDF (logical syllabus sequence)
    # Note: quiz-session-summary and help (FAQ) are excluded - links provided instead
    page_order = [
        "index",
        "instructors",
        "class-times",
        "materials",
        "grading",
        "learning-targets",
        "learning-targets-list",
        "policies",
        "resources",
    ]

    # Collect rendered pages for PDF generation
    pdf_documents = []

    for template_file in pages_dir.glob("*.html.j2"):
        page_name = template_file.stem.replace(".html", "")
        output_file = output_path / f"{page_name}.html"

        # Skip Math 197 content for courses that don't include it
        # (handled in templates with conditionals instead)

        template = env.get_template(f"pages/{template_file.name}")

        # Render template with config data
        html = template.render(
            **config,
            current_page=f"{page_name}.html",
            base_path="",  # Pages are at root of course output
        )

        output_file.write_text(html)
        print(f"  Built: {output_file.relative_to(PROJECT_ROOT)}")

        # Collect for combined PDF (exclude quiz-session-summary)
        if generate_pdf and page_name in page_order:
            pdf_documents.append((page_name, html))

    # Generate combined PDF if requested
    if generate_pdf and pdf_documents:
        from weasyprint import HTML, CSS

        # =================================================================
        # PDF FONT SIZE CONFIGURATION
        # Adjust these values to change font sizes throughout the PDF
        # =================================================================
        # Page title (course code and name in header): 9pt
        # Header subtitle: 7pt
        # H2 (main section headers like "Welcome to MATH 140B!"): 8pt
        # H3 (subsection headers): 7pt
        # H4 (sub-subsection headers): 7pt
        # Body text: 7pt
        # Table text: 6pt
        # =================================================================
        pdf_css = CSS(string="""
            @page {
                size: letter;
                margin: 0.4in 0.5in;
            }

            /* ===== BASE TYPOGRAPHY ===== */
            body {
                font-size: 7pt;
                line-height: 1.2;
            }

            /* ===== REMOVE ALL GREY/LIGHT BACKGROUNDS ===== */
            * {
                background-color: transparent !important;
            }
            /* Re-apply specific backgrounds we want to keep */
            .section-table th,
            .grade-table th,
            .xp-table th {
                background-color: #001E44 !important;
                color: white !important;
            }

            /* ===== PAGE TITLE (header) ===== */
            header {
                padding: 0.1rem 0;
                margin-bottom: 0.15rem;
                background: none !important;
                border: none !important;
            }
            header h1 {
                font-size: 9pt;
                color: #001E44;
                margin: 0;
                padding: 0;
            }
            header .subtitle {
                font-size: 7pt;
                margin-top: 0.05rem;
            }

            /* ===== HEADER HIERARCHY ===== */
            h2, main h2 {
                font-size: 8pt !important;
                margin: 0.2rem 0 0.1rem 0 !important;
                padding-bottom: 0.05rem !important;
                border-bottom: 1px solid #001E44 !important;
                page-break-after: avoid;
            }
            h3 {
                font-size: 7pt !important;
                margin: 0.15rem 0 0.08rem 0 !important;
                page-break-after: avoid;
            }
            h4 {
                font-size: 7pt !important;
                margin: 0.1rem 0 0.05rem 0 !important;
            }

            /* ===== TEXT ELEMENTS ===== */
            p {
                margin-bottom: 0.1rem;
            }
            li {
                margin-bottom: 0.03rem;
            }
            ul, ol {
                margin-left: 0.6rem;
                margin-bottom: 0.1rem;
                padding-left: 0;
            }

            /* ===== LAYOUT ===== */
            .container {
                display: block;
                padding: 0;
            }
            main {
                padding: 0;
            }
            .page-wrapper {
                min-height: auto;
            }

            /* ===== HIDE NAVIGATION ===== */
            #sidebar-navigation,
            #quick-links-sidebar,
            .sidebar-navigation,
            .quick-links,
            nav,
            footer {
                display: none !important;
            }

            /* ===== TABLES ===== */
            .data-table, .section-table, .grade-table, .xp-table {
                margin: 0.1rem 0;
            }
            .data-table th, .data-table td,
            .section-table th, .section-table td,
            .grade-table th, .grade-table td,
            .xp-table th, .xp-table td {
                padding: 0.1rem 0.2rem;
                font-size: 6pt;
            }

            /* ===== ALERT/INFO BOXES ===== */
            .alert, .info-box {
                padding: 0.15rem 0.2rem;
                margin: 0.1rem 0;
                font-size: 6pt;
                border-left-width: 2px;
            }

            /* ===== INDEX PAGE ===== */
            section {
                background: none !important;
                background-color: transparent !important;
            }
            #welcome, #course-overview, #gen-ed, #prerequisites {
                background: none !important;
                background-color: transparent !important;
            }
            .welcome-section {
                background: none !important;
                background-color: transparent !important;
                padding: 0.1rem 0;
                margin-bottom: 0.15rem;
                border-radius: 0;
            }
            .feedback-diagram {
                display: none !important;
            }
            .feedback-container {
                display: block;
            }
            .feedback-text {
                min-width: auto;
            }
            .overview-section {
                background: none !important;
                background-color: transparent !important;
                padding: 0.05rem 0;
                margin-bottom: 0.1rem;
            }
            .overview-card {
                padding: 0.1rem 0.2rem;
                margin: 0.1rem 0;
                background: none !important;
                background-color: transparent !important;
            }
            .gen-ed-objective {
                padding: 0.1rem 0.2rem;
                margin: 0.08rem 0;
                border-left-width: 2px;
                background: none !important;
                background-color: transparent !important;
            }
            .gen-ed-objective h4 {
                font-size: 7pt !important;
                margin-bottom: 0.05rem !important;
            }
            .gen-ed-objective p {
                font-size: 6pt;
            }

            /* ===== INSTRUCTORS PAGE ===== */
            .instructor-grid {
                display: block;
            }
            .instructor-card {
                padding: 0.15rem 0.2rem;
                margin-bottom: 0.15rem;
                border-left-width: 2px;
                page-break-inside: avoid;
            }
            .instructor-header {
                margin-bottom: 0.05rem;
            }
            .instructor-name {
                font-size: 7pt !important;
            }
            .instructor-title {
                font-size: 6pt !important;
            }
            .instructor-pronouns {
                font-size: 6pt;
                margin-bottom: 0.1rem;
            }
            .instructor-details {
                font-size: 6pt;
                gap: 0.08rem;
            }
            .detail-row {
                margin-bottom: 0.05rem;
            }
            .detail-label {
                min-width: 50px;
                font-size: 6pt;
            }
            .detail-content {
                font-size: 6pt;
            }
            .sections-taught {
                margin-top: 0.1rem;
                padding-top: 0.1rem;
            }
            .section-badge {
                font-size: 5pt;
                padding: 0.05rem 0.15rem;
            }
            .office-hours-list {
                margin: 0;
                padding: 0;
            }
            .office-hours-list li {
                margin-bottom: 0.03rem;
                padding-left: 0.3rem;
                font-size: 6pt;
            }
            .oh-type-badge {
                font-size: 5pt;
                padding: 0.02rem 0.1rem;
            }
            .appointment-note {
                font-size: 5pt;
                margin-top: 0.05rem;
            }
            .shared-hours-section {
                padding: 0.15rem;
                margin: 0.15rem 0;
            }
            .shared-hours-title {
                font-size: 7pt !important;
            }
            .hours-iframe {
                display: none !important;
            }

            /* ===== CLASS TIMES PAGE ===== */
            .thursday-hours-box {
                padding: 0.15rem;
                margin: 0.1rem 0;
            }
            .hours-grid {
                display: flex;
                flex-wrap: wrap;
                gap: 0.1rem;
                margin: 0.1rem 0;
            }
            .hour-slot {
                padding: 0.08rem 0.15rem;
                flex: 0 0 auto;
                min-width: 70px;
            }
            .hour-time {
                font-size: 6pt;
                margin-bottom: 0.03rem;
            }
            .hour-location {
                font-size: 5pt;
            }
            .hours-note {
                margin-top: 0.1rem;
                margin-bottom: 0.05rem;
                padding: 0.1rem;
                font-size: 5pt;
            }

            /* ===== GRADING PAGE ===== */
            .important-box, .xp-section, .example-box {
                padding: 0.15rem;
                margin: 0.1rem 0;
            }
            .math197-section {
                padding: 0.15rem;
                margin: 0.1rem 0;
            }
            .essential-targets {
                gap: 0.1rem;
                margin: 0.05rem 0;
            }
            .target-badge {
                font-size: 5pt;
                padding: 0.03rem 0.1rem;
            }

            /* ===== LEARNING TARGETS LIST ===== */
            .lt-accordion {
                margin-bottom: 0.08rem;
                box-shadow: none;
                border: none;
                border-bottom: 1px solid #eee;
            }
            .lt-accordion-header {
                padding: 0.1rem 0.15rem;
                border-left-width: 2px;
            }
            .lt-id {
                font-size: 6pt;
                min-width: 25px;
            }
            .lt-title {
                font-size: 6pt;
            }
            .type-badge {
                font-size: 5pt;
                padding: 0.02rem 0.1rem;
            }
            .expand-icon,
            .lt-accordion-content {
                display: none !important;
            }
        """)

        # Sort pages according to defined order
        def page_sort_key(item):
            page_name = item[0]
            try:
                return page_order.index(page_name)
            except ValueError:
                return len(page_order)  # Unknown pages go at the end

        pdf_documents.sort(key=page_sort_key)

        # Use public GitHub Pages URL for links in PDF
        public_base_url = f"https://rfd131.github.io/syllabi/{term}/{course}/"

        # =================================================================
        # PDF-SPECIFIC HTML TRANSFORMATIONS
        # These modify content for PDF only, not the website
        # =================================================================
        # Get course code for dynamic text replacement
        course_code = config.get("course", {}).get("code", "MATH")
        learning_targets_total = config.get("learning_targets", {}).get("total", 25)

        def transform_html_for_pdf(page_name, html):
            """Apply PDF-specific transformations to HTML content."""

            if page_name == "index":
                # Add syllabus website link after header, before Welcome section
                syllabus_link = f'''
                <div style="background-color: #e8f4fd; border: 1px solid #1E407C; border-radius: 4px; padding: 8px 12px; margin-bottom: 12px; text-align: center;">
                    <strong>Full Interactive Syllabus:</strong> <a href="{public_base_url}" style="color: #1E407C;">{public_base_url}</a>
                </div>
                '''
                # Insert after </header> and before the welcome section
                html = re.sub(
                    r'(</header>\s*)',
                    r'\1' + syllabus_link,
                    html,
                    count=1
                )

            elif page_name == "class-times":
                # Replace Thursday Quiz Hours block with simplified paragraph + link
                thursday_replacement = f'''
                <h2 id="thursday-quiz-hours">Thursday Quiz Hours</h2>
                <p>Thursday Quiz Hours are additional sessions available for Learning Targets that you have not yet been successful in during a Tuesday or midterm exam session. <strong>Thursday Quiz Hours begin in Week 4.</strong> Learning Targets become available in quiz hours after they have been available at least twice in either a Tuesday session or on a Midterm Exam.</p>
                <p><strong>See the full syllabus for times and locations:</strong> <a href="{public_base_url}class-times.html#thursday-quiz-hours">{public_base_url}class-times.html#thursday-quiz-hours</a></p>
                '''
                # Remove the thursday-hours-box div and its contents
                html = re.sub(
                    r'<h2 id="thursday-quiz-hours">.*?</div>\s*(?=\{% endif %\}|</main>|<h2|$)',
                    thursday_replacement,
                    html,
                    flags=re.DOTALL
                )

            elif page_name == "learning-targets-list":
                # Replace the learning targets list with a link
                lt_replacement = f'''
                <h2>{course_code} Learning Targets</h2>
                <p>This page lists all {learning_targets_total} Learning Targets for {course_code}. Each target represents a specific skill or concept you'll master during the course.</p>
                <p><strong>View the complete Learning Targets list on the syllabus website:</strong> <a href="{public_base_url}learning-targets-list.html">{public_base_url}learning-targets-list.html</a></p>
                '''
                # Remove everything after the intro paragraph up to </main>
                html = re.sub(
                    r'(<main>).*?(</main>)',
                    r'\1' + lt_replacement + r'\2',
                    html,
                    flags=re.DOTALL
                )

            elif page_name == "resources":
                # Add link to FAQ at the end
                faq_link = f'''
                <h2>Frequently Asked Questions</h2>
                <p>Have questions about the course? Check our FAQ page for answers to common questions about assignments, grading, office hours, and more.</p>
                <p><strong>View FAQ:</strong> <a href="{public_base_url}help.html">{public_base_url}help.html</a></p>
                '''
                # Add before </main>
                html = re.sub(
                    r'(</main>)',
                    faq_link + r'\1',
                    html
                )

            return html

        # Render each page and collect all pages
        all_pages = []
        for i, (page_name, html) in enumerate(pdf_documents):
            # Apply PDF-specific transformations
            html = transform_html_for_pdf(page_name, html)

            # Remove header/footer from all pages except the first (index)
            if i > 0:
                html = re.sub(r'<header>.*?</header>', '', html, flags=re.DOTALL)
                html = re.sub(r'<footer>.*?</footer>', '', html, flags=re.DOTALL)
            doc = HTML(string=html, base_url=public_base_url).render(stylesheets=[pdf_css])
            all_pages.extend(doc.pages)

        # Combine into single PDF
        if all_pages:
            pdf_file = output_path / "syllabus.pdf"
            # Create a document from the first page's document and replace pages
            combined_doc = HTML(string=pdf_documents[0][1], base_url=public_base_url).render(stylesheets=[pdf_css])
            combined_doc.pages[:] = all_pages
            combined_doc.write_pdf(pdf_file)
            print(f"  Built: {pdf_file.relative_to(PROJECT_ROOT)} ({len(all_pages)} pages)")

    return True


def clean_output():
    """Remove all generated files."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
        print(f"Cleaned: {OUTPUT_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Build course syllabi")
    parser.add_argument(
        "course",
        nargs="?",
        help="Specific course to build (e.g., sp26/math140b)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output directory before building",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available courses",
    )
    parser.add_argument(
        "--from-sheets",
        action="store_true",
        help="Fetch configuration from Google Sheets instead of local YAML files",
    )
    parser.add_argument(
        "--from-cache",
        action="store_true",
        help="Build from cached JSON files (no API calls)",
    )
    parser.add_argument(
        "--save-cache",
        action="store_true",
        help="Save fetched config to JSON cache (use with --from-sheets)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also generate PDF versions of each page",
    )
    args = parser.parse_args()

    from_sheets = getattr(args, "from_sheets", False)
    from_cache = getattr(args, "from_cache", False)
    save_cache = getattr(args, "save_cache", False)
    generate_pdf = getattr(args, "pdf", False)

    if args.list:
        if from_cache:
            courses = get_cached_courses()
            print("Courses with cached JSON files:")
        elif from_sheets:
            courses = get_sheets_courses()
            print("Courses configured via environment variables:")
        else:
            courses = get_all_courses()
            print("Available courses (from YAML):")
        for term, course in courses:
            print(f"  {term}/{course}")
        return

    if args.clean:
        clean_output()

    env = setup_jinja_env()

    # Determine source description
    if from_cache:
        source = "cached JSON"
    elif from_sheets:
        source = "Google Sheets"
    else:
        source = "YAML"

    if args.course:
        # Build specific course
        parts = args.course.split("/")
        if len(parts) != 2:
            print("Error: Course must be in format 'term/course' (e.g., sp26/math140b)")
            return
        term, course = parts
        print(f"Building {term}/{course} from {source}...")
        build_course(env, term, course, from_sheets=from_sheets,
                     from_cache=from_cache, save_cache=save_cache,
                     generate_pdf=generate_pdf)
    else:
        # Build all courses
        if from_cache:
            courses = get_cached_courses()
            if not courses:
                print("No cached JSON files found in data directory.")
                print("Run with --from-sheets --save-cache first to create cache.")
                return
        elif from_sheets:
            courses = get_sheets_courses()
            if not courses:
                print("No courses configured via environment variables.")
                print("Set MATHXXX_COURSE_CONFIG_ID environment variables.")
                return
        else:
            courses = get_all_courses()
            if not courses:
                print("No courses found in data directory.")
                return

        print(f"Building {len(courses)} course(s) from {source}...")
        for term, course in courses:
            print(f"\nBuilding {term}/{course}...")
            build_course(env, term, course, from_sheets=from_sheets,
                         from_cache=from_cache, save_cache=save_cache,
                         generate_pdf=generate_pdf)

    print("\nBuild complete!")


if __name__ == "__main__":
    main()
