import ast
import os


def extract_functions_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        file_content = file.read()

    # 抽象構文木（AST）を解析
    tree = ast.parse(file_content)

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 関数名とdocstringを抽出
            function_name = node.name
            docstring = ast.get_docstring(node)
            functions.append((function_name, docstring))

    return functions


def document_project(source_dir):
    documentation = {}
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                module_name = (
                    os.path.relpath(file_path, source_dir)
                    .replace(os.sep, ".")
                    .rstrip(".py")
                )
                functions = extract_functions_from_file(file_path)
                documentation[module_name] = functions

    return documentation


def print_documentation(documentation):
    for module, functions in documentation.items():
        print(f"Module: {module}")
        for function_name, docstring in functions:
            print(f"  Function: {function_name}")
            if docstring:
                print(f"    Docstring: {docstring.strip()}")
            else:
                print("    Docstring: None")
        print()


# 実行するディレクトリを指定（例: 'root_project'）
source_directory = "/path/to/root_project"
documentation = document_project(source_directory)
print_documentation(documentation)
