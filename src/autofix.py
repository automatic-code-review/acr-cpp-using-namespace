import argparse
import json

try:
    from src import review
except ImportError:
    import review


def autofix_file(path, config):
    regex_order = config['regexOrder']

    if not path.endswith((".h", ".cpp", ".hpp")):
        raise Exception("extension type not supported")

    changed, _, new_data = review.verify(path=path, regex_order=regex_order)

    if changed:
        with open(path, "w") as data:
            data.writelines(new_data)

    return changed

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--PATH', type=str, help='Path')
    parser.add_argument('--CONFIG', type=str, help='Config')

    args = parser.parse_args()

    with open(args.CONFIG, 'r') as data:
        config = json.load(data)

    autofix_file(path=args.PATH, config=config)
