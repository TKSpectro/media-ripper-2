from pathlib import Path


def rmDirRec(directory):
    if directory == Path('/') or directory == Path('/home'):
        print('Won\'t delete root or home directory!')
        return

    directory = Path(directory)
    if not directory.exists():
        return
    for item in directory.iterdir():
        if item.is_dir():
            rmDirRec(item)
        else:
            item.unlink()
    directory.rmdir()
