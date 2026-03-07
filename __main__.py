"""Allow `python -m max`."""
import json
import sys

from .daemon import main, content_cycle

if __name__ == "__main__":
    if "--once" in sys.argv:
        result = content_cycle()
        print(json.dumps(result, indent=2))
    elif "--batch" in sys.argv:
        try:
            idx = sys.argv.index("--batch")
            count = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            count = 4
        result = content_cycle(count=count)
        print(json.dumps(result, indent=2))
    elif "--test-post" in sys.argv:
        from .poster import XPoster
        poster = XPoster()
        result = poster.test_connection()
        print(json.dumps(result, indent=2))
    else:
        main()
