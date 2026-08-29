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
    if "sites" not in config:
        raise ValueError("Missing 'sites' in config/sites.json")

    sites = config["sites"]

    if not isinstance(sites, dict) or not sites:
        raise ValueError("'sites' must contain at least one site")

    for site_id, site in sites.items():
        if not site.get("domain"):
            raise ValueError(
                f"Site '{site_id}' is missing 'domain'"
            )

        if not site.get("login_url"):
            raise ValueError(
                f"Site '{site_id}' is missing 'login_url'"
            )


def copy_source(target_dir):
    if target_dir.exists():
        shutil.rmtree(target_dir)

    target_dir.mkdir(parents=True, exist_ok=True)

    for item in ROOT.iterdir():
        if item.name in EXCLUDED_NAMES:
            continue

        destination = target_dir / item.name

        if item.is_dir():
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)


def replace_domain_in_text_files(target_dir, source_domain, target_domain):
    source_domain = source_domain.rstrip("/")
    target_domain = target_domain.rstrip("/")

    for file_path in target_dir.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.suffix.lower() not in TEXT_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        updated = content.replace(source_domain, target_domain)

        if updated != content:
            file_path.write_text(
                updated,
                encoding="utf-8"
            )


def collect_pages(target_dir, domain):
    pages = []

    for index_file in target_dir.rglob("index.html"):
        relative = index_file.relative_to(target_dir)

        if relative.parts == ("index.html",):
            path = "/"
        else:
            directory = relative.parent.as_posix()
            path = f"/{directory}/"

        pages.append(path)

    return sorted(set(pages))


def create_sitemap(target_dir, domain):
    pages = collect_pages(target_dir, domain)
    today = date.today().isoformat()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "",
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "",
    ]

    for path in pages:
        url = escape(f"{domain.rstrip('/')}{path}")

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

    print(f"✓ Sitemap generated: {sitemap_file}")
    print(f"  Pages found: {len(pages)}")


def create_robots(target_dir, domain):
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

    print(f"✓ Robots generated: {robots_file}")


def build_site(site_id, site, source_domain):
    domain = site["domain"].rstrip("/")
    source_domain = source_domain.rstrip("/")

    target_dir = DIST_DIR / site_id

    print()
    print("======================================")
    print(f" BUILDING: {site_id}")
    print("======================================")
    print(f"Domain: {domain}")

    copy_source(target_dir)

    replace_domain_in_text_files(
        target_dir,
        source_domain,
        domain
    )

    create_robots(
        target_dir,
        domain
    )

    create_sitemap(
        target_dir,
        domain
    )

    print(f"✓ Build completed: {target_dir}")


def main():
    print("======================================")
    print(" KADOQQ MASTER MULTI-DOMAIN BUILDER")
    print("======================================")

    config = load_config()
    validate_config(config)

    if "source" not in config:
        raise ValueError("Missing 'source' in config/sites.json")

    if not config["source"].get("domain"):
        raise ValueError("Missing source domain in config/sites.json")

    source_domain = config["source"]["domain"]

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    for site_id, site in config["sites"].items():
        build_site(
            site_id,
            site,
            source_domain
        )

    print()
    print("======================================")
    print(" ALL BUILDS COMPLETED SUCCESSFULLY")
    print("======================================")


if __name__ == "__main__":
    main()
