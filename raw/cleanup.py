import pathlib
from csvw.dsv import reader, UnicodeWriter


def fix(p):
    if '_history' in p.stem:
        p.unlink()
        return

    rows = list(reader(p, dicts=True))
    if not rows:
        p.unlink()
        return

    remove = {'created', 'updated', 'active', 'polymorphic_type'}
    with UnicodeWriter(p) as w:
        for i, row in enumerate(rows):
            if i == 0:
                w.writerow([c for c in row.keys() if c not in remove])
            for c in remove:
                if c in row:
                    del row[c]
            w.writerow(row.values())


if __name__ == '__main__':
    for p in list(pathlib.Path('.').glob('*.csv')):
        fix(p)

