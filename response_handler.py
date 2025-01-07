import re


def parse_result(result_text, error_threshold=5):
    """
    Parses the output to extract an overall comment and probabilities for 'agrees',
    'disagrees', and 'unrelated'. If the "An error occurred" label probability exceeds
    the error_threshold, set 'error_flag' to True.

    Args:
        result_text (str): The raw result text to parse.
        error_threshold (int): The threshold percentage for triggering the error flag.

    Returns:
        dict: Parsed data with keys 'comment', 'agrees', 'disagrees',
              'unrelated', and 'error_flag'.
    """
    # Regular expressions for extracting data
    regex_patterns = {
        "comment": r"Overall Comment:\**\s+(.+)",
        "agrees": r"\| Agrees\s*\|\s*(\d+(.\d+)?)%?\s*\|",
        "disagrees": r"\| Disagrees\s*\|\s*(\d+(.\d+)?)%?\s*\|",
        "unrelated": r"\| Unrelated\s*\|\s*(\d+(.\d+)?)%?\s*\|",
        "error": r"\| An error occurred\s*\|\s*(\d+(.\d+)?)%?\s*",
    }

    # Default dictionary
    parsed_data = {
        "comment": "",
        "agrees": None,
        "disagrees": None,
        "unrelated": None,
        "error_flag": False,  # To indicate if an error threshold is exceeded
    }

    # Parse the value for each attribute
    for key, pattern in regex_patterns.items():
        try:
            match = re.search(pattern, result_text, re.IGNORECASE)
            if match:
                if key == "comment":
                    parsed_data[key] = match.group(1).strip()
                else:
                    probability = float(match.group(1).strip())
                    if key == "error" and probability > error_threshold:
                        parsed_data["error_flag"] = True
                    elif (
                        key != "error"
                    ):  # Only include agrees, disagrees, and unrelated
                        parsed_data[key] = probability
            else:
                if (
                    key != "error"
                ):  # Only flag missing keys that aren't the "error" label
                    parsed_data[key] = None
                    parsed_data["error_flag"] = True
        except Exception as e:
            if key == "error":
                continue
            # Handle unexpected parsing errors
            parsed_data["error_flag"] = True
            parsed_data["comment"] = f"Parsing failed due to error: {e}"
            break

    return parsed_data


def get_stance(analyze):
    if analyze["error_flag"]:
        return "error"
    agreement = analyze["agrees"]
    disagreement = analyze["disagrees"]
    unrelatedness = analyze["unrelated"]
    if agreement == disagreement == unrelatedness == 0:
        return "error"
    total = agreement + disagreement + unrelatedness
    agreement /= total
    disagreement /= total
    unrelatedness /= total
    if unrelatedness > agreement + disagreement + 0.35:
        stance = "unrelated"
    elif abs(agreement - disagreement) < 0.15:
        stance = "nuanced"
    elif agreement > disagreement:
        stance = "supports"
    elif disagreement > agreement:
        stance = "contradicts"
    else:
        stance = "error"
    return stance
