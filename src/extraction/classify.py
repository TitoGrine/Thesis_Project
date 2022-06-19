import numpy
import regex
from wordfreq import zipf_frequency
from src.utils import get_fuzziness_distance


def score_formula(original_length, match_length, num_errors):
    abs_diff = abs(original_length - match_length)

    return original_length / (original_length + abs_diff + 2 * num_errors)


def calculate_score(search_expression, length, string, explicit_boundaries=False):
    if explicit_boundaries:
        search_expression = f"(\W|_|\\b){search_expression}(\W|_|\\b)"
        length += 2

    match = regex.search(search_expression, string)

    if match:
        # print(f"\033[93m {match[0]} - {search_expression} \033[0m")
        return score_formula(length, len(match[0]), sum(match.fuzzy_counts))

    return 0


def get_expression_combinations(initial_expression):
    weight_sum = 0
    token_combinations = set()
    expression_combinations = set()
    initial_expression = regex.sub(r"([^\w&]|_)+", " ", initial_expression.lower()).strip()

    expression_combinations.add(initial_expression)
    expression_combinations.add(initial_expression.replace("&", "and"))
    expression_combinations.add(initial_expression.replace("&", "").strip())

    for expression in expression_combinations:
        tokens = expression.split(" ")

        if len(tokens) > 1:
            token_combinations.update(
                [token for token in tokens if len(token) > 2])

    expression_tuples = []

    for expression in expression_combinations:
        length = len(expression)

        regex_expression = "(\w){0,2}((\W|_)|(\W|_)(\w)*(\W|_)){0,2}(\w){0,2}".join(
            [f"(?b)({token}){{e<={get_fuzziness_distance(len(token))}}}" for token in expression.split(" ")])

        expression_tuples.append((regex_expression, length, 1.0))
        weight_sum += 1.0

    for token in token_combinations:
        length = len(token)
        regex_expression = "(?b)(\\b" + token + "\\b){e<=1}"
        weight = 0.25 - (zipf_frequency(token, 'en') / 32.0)

        expression_tuples.append((regex_expression, length, weight))
        weight_sum += weight

    return [(expression, length, weight / weight_sum) for expression, length, weight in expression_tuples]


def calculate_expression_score(expression, link_info):
    score = 0
    search_expressions = get_expression_combinations(expression)

    for search_expression, length, weight in search_expressions:
        matches = [
            calculate_score(search_expression, length, " ".join(link_info.get('name', [])).lower(), True),
            calculate_score(search_expression, length, " ".join(link_info.get('title', [])).lower(), True),
            calculate_score(search_expression, length, link_info.get('description', "").lower(), True),
            calculate_score(search_expression, length, " ".join(link_info.get('keywords', [])).lower(), True),
            calculate_score(search_expression, length, " ".join(link_info.get('internal_links', [])).lower()),
            calculate_score(search_expression, length, " ".join(link_info.get('external_links', [])).lower()),
            calculate_score(search_expression, length, " ".join(link_info.get('emails', [])).lower()),
            calculate_score(search_expression, length, link_info.get('corpus', "").lower(), True),
        ]

        score += (sum(matches) / 8.0) * weight

    return score


def calculate_link_profile_relatedness(link_info, profile_names):
    scores = []

    for expression in profile_names:
        scores.append(calculate_expression_score(expression, link_info))

    score = numpy.average(scores) if len(scores) > 0 else 0

    print(f"\033[91m {score}: {link_info.get('original_link', '-')} \033[0m")

    return numpy.average(scores) if len(scores) > 0 else 0
