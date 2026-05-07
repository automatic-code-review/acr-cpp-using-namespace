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


def is_preprocessor_directive(text):
    """Detecta se uma linha é uma diretiva de pré-processador de controle de fluxo"""
    stripped = text.strip()
    return bool(re.match(r'#\s*(ifdef|ifndef|elif|elseif|else|endif)', stripped))


def get_usings_with_protection_info(lines):
    """
    Extrai usings e marca quais estão protegidos por diretivas de pré-processador.
    Retorna uma lista de tuplas: (using, is_protected_by_directive)
    """
    usings_info = []
    preprocessor_depth = 0
    
    for line in lines:
        line_stripped = line.strip()
        
        if re.match(r'#\s*(ifdef|ifndef)', line_stripped):
            preprocessor_depth += 1
        elif re.match(r'#\s*endif', line_stripped):
            preprocessor_depth = max(0, preprocessor_depth - 1)
        
        if is_using_namespace(line_stripped):
            is_protected = preprocessor_depth > 0
            usings_info.append((line_stripped, is_protected))
    
    return usings_info


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
    """
    Reordena uma lista de usings conforme as regras de regex_order.
    Os usings protegidos por diretivas de pré-processador já devem ter sido removidos.
    """
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
    """
    Verifica se a ordem dos usings mudou, ignorando usings protegidos por #ifdef.
    """
    lines_using_changed = []
    lines_using_original = []
    
    usings_info_original = get_usings_with_protection_info(lines_original)
    usings_info_changed = get_usings_with_protection_info(lines_changed)

    for using, is_protected in usings_info_original:
        if not is_protected:
            lines_using_original.append(using)

    for using, is_protected in usings_info_changed:
        if not is_protected:
            lines_using_changed.append(using)

    return lines_using_original != lines_using_changed


def verify(path, regex_order):
    """
    Verifica e reordena usings, mantendo protegidos por #ifdef no lugar.
    Retorna: (changed, usings_ordered, lines_fixed)
    """
    with open(path, 'r') as data:
        lines = data.readlines()

    usings_info = get_usings_with_protection_info(lines)
    
    usings_protected = []
    usings_normal = []
    
    for using, is_protected in usings_info:
        if is_protected:
            usings_protected.append(using)
        else:
            usings_normal.append(using)
    
    usings_normal = remove_duplicate_usings(usings_normal)
    
    lines_fix = []
    preprocessor_depth = 0
    
    for line in lines:
        line_stripped = line.strip()
        
        if re.match(r'#\s*(ifdef|ifndef)', line_stripped):
            preprocessor_depth += 1
            lines_fix.append(line)
        elif re.match(r'#\s*endif', line_stripped):
            preprocessor_depth = max(0, preprocessor_depth - 1)
            lines_fix.append(line)
        elif re.match(r'#\s*(elif|elseif)', line_stripped):
            lines_fix.append(line)
        elif re.match(r'#\s*else', line_stripped):
            lines_fix.append(line)
        elif is_using_namespace(line_stripped):
            if preprocessor_depth == 0:
                continue
            else:
                lines_fix.append(line)
        else:
            lines_fix.append(line)

    usings_ordered = adjust_order(usings_normal, regex_order)

    pos_last_include = get_last_include_position(lines_fix) + 1
    lines_fix[pos_last_include:pos_last_include] = usings_ordered
    lines_fix = remove_linhas_brancas_consecutivas(lines_fix)

    if check_order_changed(lines_fix, lines):
        print(f'MUDOU ALGUMA ORDEM: {path}')
        return True, usings_ordered, lines_fix

    return False, usings_ordered, lines_fix


def ordered_to_string(ordered):
    return "<pre>"+"".join([order.replace("\n", "<br>") for order in ordered[1:-1]])+"</pre>"


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
