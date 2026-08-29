import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "sites.json"


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
        if "domain" not in site:
            raise ValueError(
                f"Site '{site_id}' is missing 'domain'"
            )

        if "login_url" not in site:
            raise ValueError(
                f"Site '{site_id}' is missing 'login_url'"
            )

        print(f"✓ Site: {site_id}")
        print(f"  Domain: {site['domain']}")
        print(f"  Login : {site['login_url']}")


def main():
    print("======================================")
    print(" KADOQQ MASTER CONFIGURATION CHECK")
    print("======================================")

    config = load_config()
    validate_config(config)

    print("--------------------------------------")
    print("Configuration check successful.")
    print("--------------------------------------")


if __name__ == "__main__":
    main()
