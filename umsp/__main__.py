from __future__ import annotations

import json

from umsp import runtime_info


def main() -> int:
    print(json.dumps(runtime_info()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
