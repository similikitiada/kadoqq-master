import json
import shutil
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "sites.json"
DIST_DIR = ROOT / "dist"


# File/folder yang tidak ikut disalin ke hasil website
EXCLUDED_NAMES = {
    ".git",
    ".github",
    "config",
    "scripts",
    "dist",
    "README.md",
}


# File teks yang aman untuk diproses
TEXT_EXTENSIONS = {
    ".html",
    ".htm",
    ".txt",
    ".xml",
    ".json",
    ".webmanifest",
    ".css",
    ".js",
}


def load_config():
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_FILE}"
        )

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_config(config):
    # Validasi source
    if "source" not in config:
        raise ValueError(
            "Missing 'source' in config/sites.json"
        )

    source = config["source"]

    if not source.get("domain"):
        raise ValueError(
            "Missing source domain in config/sites.json"
        )

    if not source.get("login_url"):
        raise ValueError(
            "Missing source login_url in config/sites.json"
        )

    # Validasi sites
    if "sites" not in config:
        raise ValueError(
            "Missing 'sites' in config/sites.json"
        )

    sites = config["sites"]

    if not isinstance(sites, dict) or not sites:
        raise ValueError(
            "'sites' must contain at least one site"
        )
    for site_id, site in sites.items():

        if not site.get("domain"):
            raise ValueError(
                f"Site '{site_id}' is missing 'domain'"
            )

        if not site.get("login_url"):
            raise ValueError(
                f"Site '{site_id}' is missing 'login_url'"
            )

        if "deploy" not in site:
            raise ValueError(
                f"Site '{site_id}' is missing 'deploy'"
            )

        if not isinstance(site["deploy"], bool):
            raise ValueError(
                f"Site '{site_id}' 'deploy' must be true or false"
            )


def copy_source(target_dir):
    if target_dir.exists():
        shutil.rmtree(target_dir)

    target_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    for item in ROOT.iterdir():

        if item.name in EXCLUDED_NAMES:
            continue

        destination = target_dir / item.name

        if item.is_dir():
            shutil.copytree(
                item,
                destination
            )
        else:
            shutil.copy2(
                item,
                destination
            )


def replace_text(
    target_dir,
    source_text,
    target_text
):
    source_text = source_text.rstrip("/")
    target_text = target_text.rstrip("/")

    for file_path in target_dir.rglob("*"):

        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            continue

        updated = content.replace(
            source_text,
            target_text
        )

        if updated != content:
            file_path.write_text(
                updated,
                encoding="utf-8"
            )


def collect_pages(target_dir):
    pages = []

    for index_file in target_dir.rglob("index.html"):

        relative = index_file.relative_to(
            target_dir
        )

        if relative.parts == ("index.html",):

            path = "/"

        else:

            directory = relative.parent.as_posix()
            path = f"/{directory}/"

        pages.append(path)

    return sorted(set(pages))


def create_sitemap(
    target_dir,
    domain
):
    pages = collect_pages(target_dir)
    today = date.today().isoformat()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "",
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "",
    ]

    for path in pages:

        url = escape(
            f"{domain.rstrip('/')}{path}"
        )

        lines.extend([
            "    <url>",
            f"        <loc>{url}</loc>",
            f"        <lastmod>{today}</lastmod>",
            "    </url>",
            "",
        ])

    lines.append("</urlset>")

    sitemap_file = target_dir / "sitemap.xml"

    sitemap_file.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print(
        f"✓ Sitemap generated: {sitemap_file}"
    )

    print(
        f"  Pages found: {len(pages)}"
    )


def create_robots(
    target_dir,
    domain
):
    robots_content = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {domain.rstrip('/')}/sitemap.xml\n"
    )

    robots_file = target_dir / "robots.txt"

    robots_file.write_text(
        robots_content,
        encoding="utf-8"
    )

    print(
        f"✓ Robots generated: {robots_file}"
    )


def build_site(
    site_id,
    site,
    source_domain,
    source_login_url
):
    domain = site["domain"].rstrip("/")

    target_login_url = site["login_url"].rstrip("/")

    source_domain = source_domain.rstrip("/")

    source_login_url = source_login_url.rstrip("/")

    target_dir = DIST_DIR / site_id

    print()
    print("======================================")
    print(f" BUILDING: {site_id}")
    print("======================================")

    print(
        f"Domain: {domain}"
    )

    print(
        f"Login : {target_login_url}"
    )

    # Copy source website
    copy_source(target_dir)

    # Replace source domain
    replace_text(
        target_dir,
        source_domain,
        domain
    )

    # Replace source login URL
    replace_text(
        target_dir,
        source_login_url,
        target_login_url
    )

    # Generate robots.txt
    create_robots(
        target_dir,
        domain
    )

    # Generate sitemap.xml
    create_sitemap(
        target_dir,
        domain
    )

    print(
        f"✓ Build completed: {target_dir}"
    )


def main():

    print("======================================")
    print(" KADOQQ MASTER MULTI-DOMAIN BUILDER")
    print("======================================")

    # Load configuration
    config = load_config()

    # Validate configuration
    validate_config(config)

    # Source configuration
    source_domain = config["source"]["domain"]

    source_login_url = config["source"]["login_url"]

    # Reset dist directory
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Build every configured site
    for site_id, site in config["sites"].items():

        build_site(
            site_id,
            site,
            source_domain,
            source_login_url
        )

    print()
    print("======================================")
    print(" ALL BUILDS COMPLETED SUCCESSFULLY")
    print("======================================")


if __name__ == "__main__":
    main()
