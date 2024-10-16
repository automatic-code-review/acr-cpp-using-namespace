import os.path
import re

import automatic_code_review_commons as commons


def remove_duplicate_usings(usings):
    retorno = []

    for using in usings:
        if using not in retorno:
            retorno.append(using)

    return retorno


def is_using_namespace(text):
    if not text.startswith('using '):
        return False

    if "=" in text:
        return False

    text = text.replace("using ", "")
    parts = text.split(":")

    if len(parts) == 3 and parts[0] == parts[2].replace(";", ""):
        return False

    return True


def remove_linhas_brancas_consecutivas(lista_strings):
    resultado = []
    linhas_em_branco = 0

    for linha in lista_strings:
        if linha.strip() == "":
            linhas_em_branco += 1
            if linhas_em_branco == 1:
                resultado.append(linha)
        else:
            linhas_em_branco = 0
            resultado.append(linha)

    return resultado


def adjust_order(using_list, regex_order):
    using_list_ordered = []
    regex_order_copy = []
    regex_order_copy.extend(regex_order)

    for regex_obj in regex_order_copy:
        using_by_group = []

        for regex in regex_obj['regex']:
            not_add_list = []
            using_by_current = []

            for using_current in using_list:
                if re.match(regex, using_current):
                    using_by_current.append(f"{using_current}\n")
                else:
                    not_add_list.append(using_current)

            if regex_obj['orderType'] == 'individual':
                using_by_current.sort()

            using_by_group.extend(using_by_current)
            using_list = not_add_list

        if regex_obj['orderType'] == 'group':
            using_by_group.sort()

        using_list_ordered.extend(using_by_group)
        using_list_ordered.append("\n")

        using_list_ordered = remove_linhas_brancas_consecutivas(using_list_ordered)

    return using_list_ordered


def get_last_include_position(lines):
    include_pos = -1

    pos = 0
    for line in lines:
        if line.startswith("#include ") and ".moc" not in line:
            include_pos = pos

        pos += 1

    return include_pos


def check_order_changed(lines_changed, lines_original):
    lines_using_changed = []
    lines_using_original = []

    for line in lines_original:
        line = line.strip()

        if is_using_namespace(line):
            lines_using_original.append(line)

    for line in lines_changed:
        line = line.strip()

        if is_using_namespace(line):
            lines_using_changed.append(line)

    return lines_using_original != lines_using_changed


def verify(path, regex_order):
    with open(path, 'r') as data:
        lines = data.readlines()

    usings = []
    lines_fix = []

    for line in lines:
        line_stripped = line.strip()

        if is_using_namespace(line_stripped):
            usings.append(line_stripped)
        else:
            lines_fix.append(line)

    usings = remove_duplicate_usings(usings)

    pos_last_include = get_last_include_position(lines_fix) + 1
    usings_ordered = adjust_order(usings, regex_order)

    lines_fix[pos_last_include:pos_last_include] = usings_ordered
    lines_fix = remove_linhas_brancas_consecutivas(lines_fix)

    if check_order_changed(lines_fix, lines):
        print(f'MUDOU ALGUMA ORDEM: {path}')
        return True, usings_ordered, lines_fix

    return False, usings_ordered, lines_fix


def ordered_to_string(ordered):
    strings = []
    for order in ordered:
        strings.append(f"- `{order}`")

    return "<br>".join(strings)


def review(config):
    regex_order = config['regexOrder']
    path_source = config['path_source']
    changes = config['merge']['changes']
    comment_description_pattern = config['message']

    comments = []

    for change in changes:
        if change['deleted_file']:
            continue

        new_path = change['new_path']

        if not new_path.endswith((".h", ".cpp", ".c", ".h")):
            continue

        path = os.path.join(path_source, new_path)
        changed, ordered, _ = verify(path=path, regex_order=regex_order)

        if not changed:
            continue

        comment_path = new_path
        comment_description = f"{comment_description_pattern}"
        comment_description = comment_description.replace("${FILE_PATH}", comment_path)
        comment_description = comment_description.replace("${ORDERED}", ordered_to_string(ordered))

        comments.append(commons.comment_create(
            comment_id=commons.comment_generate_id(comment_description),
            comment_path=comment_path,
            comment_description=comment_description,
            comment_snipset=False,
            comment_end_line=1,
            comment_start_line=1,
            comment_language=None,
        ))

    return comments
