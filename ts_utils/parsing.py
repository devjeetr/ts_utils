import json
import os
from collections import defaultdict
from pathlib import Path
from typing import List, Mapping, Optional, Tuple, Union

from git.repo import Repo
from tqdm.auto import tqdm
from tree_sitter import Language, Parser, Tree

__all__ = [
    'parse',
    'get_supertype_mappings',
    'get_node_types',
]

SUPPORTED_LANGUAGES = {"java", "python", "javascript"}


# tree-sitter grammar repo management
def clone_repo(repo_url: str, repo_path: str):
    def make_progress():
        bar = tqdm()
        total = None

        def progress_reporter(op_code, curr_count, max_count, message):
            nonlocal total
            if total is None:
                total = max_count
                bar.reset(total=total)

            bar.update(curr_count)

            if curr_count == max_count:
                bar.close()

        return progress_reporter

    repo = Repo.clone_from(repo_url, repo_path, progress=make_progress())
    del repo


def get_repo_path(cache_dir: str, language: str):
    return os.path.join(cache_dir, f"tree-sitter-{language}")


def get_node_types(language: str, cache_dir: str = None) -> dict:
    if not cache_dir:
        cache_dir = get_default_cache_dir()

    repo_path = cache_dir / f"tree-sitter-{language}"

    node_type_path = repo_path / "src/node-types.json"

    assert os.path.exists(node_type_path), f"Node type file doesn't exist"

    with open(node_type_path) as f:
        return json.load(f)


def download_language_repo(cache_dir: str, language: str):
    repo_name = f"tree-sitter-{language}"
    repo_path = get_repo_path(cache_dir, language)
    clone_repo(f"https://github.com/tree-sitter/{repo_name}", repo_path)


def build_language_library(cache_dir: str, library_path: str):
    language_repo_paths = []
    for language in SUPPORTED_LANGUAGES:
        repo_path = get_repo_path(cache_dir, language)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        if not os.path.exists(repo_path):
            download_language_repo(cache_dir, language)
        language_repo_paths.append(repo_path)

    Language.build_library(library_path, language_repo_paths)


def get_default_cache_dir():
    return Path().home() / ".cache" / "tree-sitter-grammars"


def load_grammar(
    language: str,
    cache_dir: Optional[str] = None,
    language_library: Optional[str] = None,
):
    if not cache_dir:
        cache_dir = Path().home() / ".cache" / "tree-sitter-grammars"
    if not language_library:
        language_library = "language_lib.so"

    assert (
        language in SUPPORTED_LANGUAGES
    ), f"Invalid language, can be one of [{', '.join(SUPPORTED_LANGUAGES)}]"
    language_library = os.path.join(cache_dir, language_library)
    if not os.path.exists(language_library):
        print(f"Building language library")
        build_language_library(cache_dir=cache_dir,
                               library_path=language_library)

    return Language(language_library, language)


def make_parser(
    language: str,
    cache_dir: Optional[str] = None,
    language_library: Optional[str] = None,
) -> Parser:
    """Creates a tree-sitter parser for the given language. If
    the language library is not specified, it will download the language
    grammar from github and cache it. Subsequent calls will reuse the
    cached grammar.
    """
    grammar = load_grammar(language,
                           cache_dir=cache_dir,
                           language_library=language_library)
    parser: Parser = Parser()
    parser.set_language(grammar)

    return parser


def parse(
    source: str,
    parser_or_language: Union[str, Parser],
    cache_dir=None,
    source_encoding="utf-8",
) -> Tree:
    if isinstance(parser_or_language, str):
        parser = make_parser(language=parser_or_language, cache_dir=cache_dir)
    else:
        parser = parser_or_language

    return parser.parse(bytes(source, encoding=source_encoding))


def get_supertype_mappings(
    language: str,
    cache_dir: Optional[str] = None
) -> Tuple[Mapping[str, List[str]], Mapping[str, str]]:
    """Loads node <-> supertype mappings for give programming language. This
    is obtained from node-types.json file, if included within the repository.

    Parameters
    ----------
    language : str
        programming language
    cache_dir : str, optional
        cache dir to use for ts git repos, by default None

    Returns
    -------
    Tuple[Mapping[str, List[str]], Mapping[str, str]]
        super_type to subtypes, subtype to supertype
    """
    node_types = get_node_types(language, cache_dir=cache_dir)

    node_to_supertype = {}
    supertype_to_node = defaultdict(list)
    for node_type in node_types:
        for subtype_info in node_type.get("subtypes", []):
            supernode_type = node_type["type"]
            subtype = subtype_info["type"]
            node_to_supertype[subtype] = supernode_type
            supertype_to_node[supernode_type].append(subtype)

    supertype_to_node = dict(supertype_to_node)

    return supertype_to_node, node_to_supertype
