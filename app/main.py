from __future__ import annotations
import argparse
from app.core.pipeline import Pipeline


def main():
    parser = argparse.ArgumentParser(description="Run Course AI Pipeline")
    parser.add_argument('folder', help='Folder containing course files')
    args = parser.parse_args()
    pipeline = Pipeline(args.folder)
    pipeline.run()


if __name__ == '__main__':
    main()
