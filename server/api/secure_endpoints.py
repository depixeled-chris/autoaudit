"""Script to add authentication to all endpoints in states.py and preambles.py"""
import re
import sys
from pathlib import Path

def secure_file(filepath):
    """Add get_current_user dependency to all route handlers"""
    with open(filepath, 'r') as f:
        content = f.read()

    # Add import for Dict and get_current_user if not present
    if 'from typing import' in content and ', Dict' not in content:
        content = re.sub(
            r'from typing import ([^\n]+)',
            r'from typing import \1, Dict',
            content
        )

    if 'get_current_user' not in content:
        content = re.sub(
            r'from api\.dependencies import get_db',
            r'from api.dependencies import get_db, get_current_user',
            content
        )

    # Pattern to match route handlers and add current_user dependency
    # Matches: async def function_name(\n    params,\n    db: ComplianceDatabase = Depends(get_db)\n):
    pattern = r'(async def \w+\([^)]*db: ComplianceDatabase = Depends\(get_db\))\s*\):'
    replacement = r'\1,\n    current_user: Dict = Depends(get_current_user)\n):'

    # Only replace if current_user is not already present
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if this is a route handler definition
        if 'async def ' in line and i + 1 < len(lines):
            # Look ahead to find the closing parenthesis
            func_def = line
            j = i + 1
            while j < len(lines) and '):' not in lines[j]:
                func_def += '\n' + lines[j]
                j += 1
            if j < len(lines):
                func_def += '\n' + lines[j]

            # Check if current_user already in this function
            if 'current_user' not in func_def and 'Depends(get_db)' in func_def:
                # Add current_user before the closing paren
                for k in range(i, j):
                    result.append(lines[k])

                # Add current_user before the closing ):\
                closing_line = lines[j]
                if closing_line.strip() == '):':
                    result.append('    current_user: Dict = Depends(get_current_user)')
                    result.append(closing_line)
                else:
                    result.append(closing_line.replace('):', ',\n    current_user: Dict = Depends(get_current_user)\n):'))
                i = j + 1
                continue

        result.append(line)
        i += 1

    content = '\n'.join(result)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Secured {filepath}")

if __name__ == "__main__":
    base_path = Path(__file__).parent
    secure_file(base_path / "states.py")
    secure_file(base_path / "preambles.py")
    print("Done securing endpoints")
