def get_creator(record: dict) -> list:
    match record:
        case {'type': 'book', 'api': 2, 'authors': [*names]}:
            return names
        case {'type': 'book', 'api': 1, 'author': name}:
            return [name]
        case {'type': 'book'}:
            return ValueError(f"Invalid 'book' record: {record!r}")
        case {'type': 'movie', 'director': name}:
            return [name]
        case _:
            raise ValueError(f'Invalid record: {record!r}')


if __name__ == '__main__':
    bi = dict(api=1, )

    x = type('Span', (), {'data': 1, 'meth': (lambda z, y: z.data + y)})
    i = x()
    print('Start', f'x: {x}', f'i: {i}', f'i.data: {i.data}', f'i.meth(2): {i.meth(2)}', sep='\n...')
