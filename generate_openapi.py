"""Generate OpenAPI 3.0 specification."""

import json
import yaml
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

from api.main import app


def generate_openapi_spec():
    """Generate and save OpenAPI specification."""

    # Get OpenAPI schema from FastAPI
    openapi_schema = app.openapi()

    # Save as JSON
    json_path = Path("openapi.json")
    with open(json_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"[OK] Generated OpenAPI JSON: {json_path}")

    # Save as YAML
    yaml_path = Path("openapi.yaml")
    with open(yaml_path, "w") as f:
        yaml.dump(openapi_schema, f, sort_keys=False, default_flow_style=False)
    print(f"[OK] Generated OpenAPI YAML: {yaml_path}")

    # Print summary
    print(f"\nAPI Summary:")
    print(f"  Title: {openapi_schema['info']['title']}")
    print(f"  Version: {openapi_schema['info']['version']}")
    print(f"  Endpoints: {len(openapi_schema['paths'])}")
    print(f"  Models: {len(openapi_schema['components']['schemas'])}")

    # List endpoints
    print(f"\nEndpoints:")
    for path, methods in openapi_schema['paths'].items():
        for method in methods.keys():
            if method in ['get', 'post', 'put', 'patch', 'delete']:
                print(f"  {method.upper():6} {path}")


if __name__ == "__main__":
    generate_openapi_spec()
