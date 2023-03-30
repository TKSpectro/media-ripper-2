from pathlib import Path


def rmDirRec(directory):
    directory = Path(directory)
    if not directory.exists():
        return
    for item in directory.iterdir():
        if item.is_dir():
            rmDirRec(item)
        else:
            item.unlink()
    directory.rmdir()
