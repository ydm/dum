import io
import os

from functools import wraps
from tempfile import NamedTemporaryFile
from typing import List, Tuple

import pandas as pd


# +--------+
# | Checks |
# +--------+

def is_valid_egn(egn):
    weights = [2, 4, 8, 5, 10, 9, 7, 3, 6]
    check_digit = int(egn[-1])
    calculated_check_digit = sum(
        [int(egn[i]) * weights[i] for i in range(9)]
    ) % 11 % 10
    return check_digit == calculated_check_digit


def perform_checks(xs: pd.DataFrame) -> List[str]:
    # Lowercase colum names.
    xs = xs.rename(columns={c: c.lower() for c in xs.columns})
    # Check column names.
    lower = set(xs.columns)
    # for want in ['номер на страница', 'име', 'егн', 'адрес', 'дата']:
    for want in ['номер на страница', 'име', 'егн', 'адрес']:
        if want not in lower:
            return [
                ('INVALID_COLUMN_NAMES',
                 f'колоната {want} липсва')
            ]
    # Perform column based checks.
    def f(column, check):
        problematic = []
        def g(row):
            try:
                ans = check(row[column])
            except:
                problematic.append(int(row.name) + 1)
            else:
                if ans is False:
                    problematic.append(int(row.name) + 1)
        return problematic, g
    errors = []
    # Check if all address pages are integers.
    prob, g = f('номер на страница', int)
    xs.apply(g, axis=1)
    if prob:
        errors.append(('INVALID_PAGE_NUMBER',) + tuple(prob))
    # Check for at least 1 space in the name.
    prob, g = f('име', lambda s: s.count(' ') >= 1)
    xs.apply(g, axis=1)
    if prob:
        errors.append(('INVALID_NAME',) + tuple(prob))
    # Check if all EGNs are valid.
    prob, g = f('егн', lambda x: is_valid_egn(list(map(int, str(x)))))
    xs.apply(g, axis=1)
    if prob:
        errors.append(('INVALID_EGN',) + tuple(prob))
    # Check if all addresses contain at least a single digit.
    prob, g = f('адрес', lambda x: any(map(str.isdigit, x)))
    xs.apply(g, axis=1)
    if prob:
        errors.append(('INVALID_ADDRESS',) + tuple(prob))
    return errors


# +---------+
# | Reading |
# +---------+

def extract_ext(fn: str) -> str:
    segments = os.path.splitext(fn)
    last = segments[-1]
    stripped = last.lstrip('.')
    return stripped.lower()


def read_table(name: str, content: io.BytesIO) -> pd.DataFrame:
    ext = extract_ext(name)
    if ext == 'xlsx':
        return pd.read_excel(content)
    elif ext == 'ods':
        return pd.read_excel(content, engine='odf')
    elif ext == 'csv':
        return pd.read_csv(io.StringIO(content.read().decode('utf-8')))


ERRORS = {
    'FILE_HAS_NO_EXTENSION': 'файлът няма разширение',
    'FILE_EXTENSION_NOT_SUPPORTED': 'разширението на файла не се поддържа',

    'INVALID_ADDRESS': '"Адрес" без цифри на ред(ове): ',
    'INVALID_COLUMN_NAMES': 'Липсващи колони: ',
    'INVALID_EGN': 'Невалидно "ЕГН" на ред(ове): ',
    'INVALID_NAME': '"Име" без шпация на ред(ове): ',
    'INVALID_PAGE_NUMBER': '"Номер на страница" не съдържа само и единствено цифри, ред(ове): ',
}


# TODO
HINTS = {
    ', очакваме: [Номер на страница, Име, ЕГН, Адрес, Дата]'
}


def transform_errors(f):
    def fmt(errtup):
        if not isinstance(errtup, Tuple):
            errtup = (errtup,)
        error = ERRORS[errtup[0]]
        suffix = ','.join(map(str, errtup[1:]))
        return f'{error}{suffix}'
    @wraps(f)
    def wrapper(*a, **kw):
        return [fmt(x) for x in f(*a, **kw)]
    return wrapper


# +------------+
# | Public API |
# +------------+

@transform_errors
def check(name: str, content: bytes) -> List[str]:
    if not '.' in name:
        return ['FILE_HAS_NO_EXTENSION']
    xs = read_table(name, content)
    if xs is None:
        return ['FILE_EXTENSION_NOT_SUPPORTED']
    return perform_checks(xs)
