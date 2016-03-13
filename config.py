

tags_pattern = {
    'p': '\n{p}\n',
    'h1': '\n\n{h1}\n',
    'h2': '\n\n{h2}\n',
    'h3': '\n\n{h3}\n',
    'h4': '\n\n{h4}\n',
    'h5': '\n\n{h5}\n',
    'h6': '\n\n{h6}\n',
    'pre': '\n{pre}\n',
    'br': '{br}\n',
}
url_pattern = {
    'a': '{a}[{url}]',
}

file_format = {
    'max_length': 80,
    'replace_list': ['.htm', '.html', '.shtml', '.php'],  # При создании файла будут заменяться на format_file
    'format_file': 'txt'
}

CONST_TEXT_TAGS = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 's', 'strike', 'b', 'strong',
                   'i', 'em', 'pre', 'sup', 'sub', 'br', 'nobr', 'span', 'code', 'table',
                   'tr', 'td', 'dl', 'dt', 'dd']
