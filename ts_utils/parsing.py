"""Utilities for managing retrieval, building and caching of tree-sitter grammars.

`tree-sitter` requires the user to build a parser for each language they want to parse.
This can be quite cumbersome, when dealing with multiple languages, changing versions
of language grammars etc. This module provides a set of utilities to make this process
quick and painless.

"""
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import List, Mapping, Optional, Tuple, Union

from git.repo import Repo
from loguru import logger
from tqdm.auto import tqdm
from tree_sitter import Language, Parser, Tree
import dataclasses

__all__ = [
    "download_language_repo",
    "load_grammar",
    "parse",
    "make_parser",
    "get_supertype_mappings",
    "get_node_types",
]

SUPPORTED_LANGUAGES = {"java", "python", "javascript", "cpp"}

_PathLike = str | Path


@dataclasses.dataclass(frozen=True, slots=True)
class LanguageCache:
    root: _PathLike
    languages: Mapping[str, str]


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

    logger.debug(
        "Cloning {repo_url} to {repo_path}", repo_url=repo_url, repo_path=repo_path
    )
    repo = Repo.clone_from(repo_url, repo_path, progress=make_progress())
    del repo


def get_repo_path(cache_dir: str, language: str):
    return os.path.join(cache_dir, f"tree-sitter-{language}")


def get_node_types(language: str, cache_dir: Optional[str | Path] = None) -> dict:
    if cache_dir:
        resolved_cache_dir = Path(cache_dir)
    else:
        resolved_cache_dir = get_default_cache_dir()

    repo_path = resolved_cache_dir / f"tree-sitter-{language}"

    node_type_path = repo_path / "src/node-types.json"

    assert os.path.exists(node_type_path), f"Node type file doesn't exist"

    with open(node_type_path) as f:
        return json.load(f)


def download_language_repo(cache_dir: str, language: str):
    repo_name = f"tree-sitter-{language}"
    repo_path = get_repo_path(cache_dir, language)
    clone_repo(f"https://github.com/tree-sitter/{repo_name}", repo_path)


def build_language_library(cache_dir: _PathLike, library_path: str | Path):
    language_repo_paths = []
    for language in SUPPORTED_LANGUAGES:
        repo_path = get_repo_path(str(cache_dir), language)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        if not os.path.exists(repo_path):
            download_language_repo(cache_dir, language)
        language_repo_paths.append(repo_path)

    Language.build_library(str(library_path), language_repo_paths)


def get_default_cache_dir():
    return Path().home() / ".cache" / "tree-sitter-grammars"


def load_grammar(
    language: str,
    cache_dir: Optional[str | Path] = None,
    language_library: Optional[str] = None,
):
    if not cache_dir:
        resolved_cache_dir = get_default_cache_dir()
    else:
        resolved_cache_dir = Path(cache_dir)

    if not language_library:
        language_library = "language_lib.so"

    assert (
        language in SUPPORTED_LANGUAGES
    ), f"Invalid language, can be one of [{', '.join(SUPPORTED_LANGUAGES)}]"

    resolved_language_library_path = resolved_cache_dir / language_library

    if not resolved_language_library_path.exists():
        logger.debug(
            "Building language library, cache_dir={cache_dir}, library_path={library_path}",
            cache_dir=resolved_cache_dir,
            library_path=resolved_language_library_path,
        )
        build_language_library(
            cache_dir=resolved_cache_dir, library_path=resolved_language_library_path
        )

    return Language(str(resolved_language_library_path), language)


def make_parser(
    language: str,
    cache_dir: Optional[str] = None,
    language_library: Optional[str] = None,
) -> Parser:
    """Creates a tree-sitter parser for the given language. If
    the language library is not specified, it will download the language
    grammar from github and cache it. Subsequent calls will reuse the
    cached grammar.

    Args:
        language: language short name
        cache_dir: directory in which to cache language repository and library. Defaults to None.
        language_library: language library from which the grammar should be loaded. Defaults to None.

    Returns:
        tree-sitter parser for the provided language
    """
    grammar = load_grammar(
        language, cache_dir=cache_dir, language_library=language_library
    )
    parser: Parser = Parser()
    parser.set_language(grammar)

    return parser


def parse(
    source: Union[str, bytes],
    parser_or_language: Union[str, Parser],
    cache_dir=None,
    source_encoding="utf-8",
) -> Tree:
    if isinstance(parser_or_language, str):
        parser = make_parser(language=parser_or_language, cache_dir=cache_dir)
    else:
        parser = parser_or_language
    if isinstance(source, str):
        source_bytes = source.encode(source_encoding)
    else:
        source_bytes = source
    return parser.parse(source_bytes)


def get_supertype_mappings(
    language: str, cache_dir: Optional[str] = None
) -> Tuple[Mapping[str, List[str]], Mapping[str, str]]:
    """Loads node <-> supertype mappings for give programming language.

    This is obtained from node-types.json file, if included within the repository(refer
    [Static Nodetypes](https://tree-sitter.github.io/tree-sitter/using-parsers#static-node-types)).
    Args:
        language: language to load mappings for
        cache_dir: directory to use for caching language repositories. Defaults to None.

    Returns:
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
