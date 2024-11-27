
def get_inner_spec(column_name, spec):
    brackets = 0
    offset = len(column_name)

    for i, ch in enumerate(spec[offset:], offset):
        if ch == '(':
            brackets += 1

        elif ch == ')':
            brackets -= 1

        if brackets == 0:
            break

    return spec[offset + 1:i]


def get_inner_columns(column_name, spec):
    inner_spec = get_inner_spec(column_name, spec)
    brackets = 0
    column_begin = 0

    columns = []
    for i, x in enumerate(inner_spec + ','):
        if x == ',':
            if brackets == 0:
                columns.append(inner_spec[column_begin:i])
                column_begin = i + 1
        elif x == '(':
            brackets += 1
        elif x == ')':
            brackets -= 1
        elif x == ' ':
            if brackets == 0:
                column_begin = i + 1
    return columns


def get_inner_columns_with_types(column_name, spec):
    inner_spec = get_inner_spec(column_name, spec)
    inner_spec = inner_spec.strip()
    brackets = 0
    prev_comma = 0
    prev_space = 0

    columns = []
    for i, x in enumerate(inner_spec.strip() + ','):
        if x == ',':
            if brackets == 0:
                columns.append((
                    inner_spec[prev_comma:prev_space].strip(),
                    inner_spec[prev_space:i]
                ))
                prev_comma = i + 1
        elif x == '(':
            brackets += 1
        elif x == ')':
            brackets -= 1
        elif x == ' ':
            if brackets == 0:
                prev_space = i + 1
    return columns
