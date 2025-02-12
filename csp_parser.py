from configparser import ConfigParser
import json


def read_ini_file(file_path):
    ext_config = ConfigParser(strict=False, allow_no_value=True, empty_lines_in_values=False)
    ext_config.optionxform = str
    ext_config.read(file_path)
    return {section: dict(items for items in ext_config.items(section)) for section in ext_config.sections()}



def read_json_file(file_path):
    """
    Reads a JSON file and returns its content.

    Args:
    file_path (str): The path to the JSON file.

    Returns:
    dict: A dictionary representation of the JSON file.
    """
    with open(file_path, 'r') as file:
        return json.load(file)

    

def process_data(ini_data, json_template):
    """
    Processes the INI data against the JSON template and extracts relevant information.

    Args:
    ini_data (dict): Dictionary containing INI file data.
    json_template (dict): JSON template for processing the data.

    Returns:
    dict: Extracted data based on the JSON template.
    """
    print("Starting data processing")
    result = {}
    for category, category_details in json_template.items():
        print(f"Processing category: {category}")
        cat_result = process_category(ini_data, category_details)
        if cat_result:
            result[category] = cat_result
    print("Processing completed")
    return result



def process_category(ini_data, category_details):
    """
    Processes a single category of data based on the given details.

    Args:
    ini_data (dict): Dictionary containing INI file data.
    category_details (dict): Details of the category to be processed.

    Returns:
    dict: Result of processing the category.
    """
    category_result = {}

    # Handle sub-categories
    if 'childs' in category_details:
        for sub_category, sub_details in category_details["childs"].items():
            print(f"  Processing sub-category: {sub_category}")
            if 'childs' in sub_details:
                sub_result = process_category(ini_data, sub_details)
                if sub_result:
                    category_result[sub_category] = sub_result
            else:
                process_sub_category(ini_data, sub_details, sub_category, category_result)
    else:
        # Directly check the tags of the current category
        tag = category_details.get("tag", "").strip("[]")
        tags = category_details.get("tags", [])
        if not tags and tag:
            tags = [tag]

        # If a tag is found, assign True to the category
        if any(tag.strip("[]") in ini_data for tag in tags):
            return True

    return {k: v for k, v in category_result.items() if v}



def process_sub_category(ini_data, sub_details, sub_category, category_result):
    """
    Processes a sub-category of data based on the given details.
    """
    tag = sub_details.get("tag", "").strip("[]")
    tags = sub_details.get("tags", [])
    if not tags and tag:
        tags = [tag]

    foreach = sub_details.get("foreach", False)
    only_one = sub_details.get("only_one", False)

    if foreach:
        process_foreach_sub_category(ini_data, sub_details, sub_category, category_result, tags, only_one)
    else:
        process_single_sub_category(ini_data, sub_details, sub_category, category_result, tags)
        
        

def process_foreach_sub_category(ini_data, sub_details, sub_category, category_result, tags, only_one):
    """
    Processes a sub-category of data with 'foreach' logic.
    """
    found = False
    sub_category_result = {}

    if tags[0].endswith("..."):
        # Pour les tags avec '...'
        exact_tag = tags[0].strip("[].")
        index = 0
        for ini_tag in ini_data.keys():
            if ini_tag == exact_tag:
                if process_conditions(ini_data, sub_details, ini_tag, sub_category_result, index, only_one):
                    found = True
                    if only_one:
                        break
                index += 1
    else:
        # Pour les tags normaux avec indexation
        index = 0
        not_found_count = 0
        while not_found_count < 2:
            foreach_tag = tags[0].replace("_N", f"_{index}")
            if foreach_tag in ini_data:
                if process_conditions(ini_data, sub_details, foreach_tag, sub_category_result, index, only_one):
                    found = True
                    if only_one:
                        category_result[sub_category] = True
                        return  # Sortie immédiate si une condition est remplie et only_one est vrai
                not_found_count = 0
            else:
                not_found_count += 1
            index += 1

    if not only_one:
        category_result[sub_category] = sub_category_result
    elif not found:
        category_result[sub_category] = False



def process_single_sub_category(ini_data, sub_details, sub_category, category_result, tags):
    """
    Processes a single sub-category of data.
    """
    entry = sub_details.get("entry")
    entries = sub_details.get("entries", {})
    return_value = sub_details.get("return_value", False)
    print(ini_data)
    # Vérifie si les conditions dans 'entries' sont remplies
    for tag in tags:
        tag = tag.strip("[]")
        if tag in ini_data:
            conditions_met = True
            if entries:
                for k, v in entries.items():
                    possible_values = v.split('|')
                    ini_value = ini_data[tag].get(k, None)
                    if not any(val.strip() == ini_value for val in possible_values):
                        conditions_met = False
                        break
            
            if conditions_met:
                if return_value and entry:
                    if isinstance(entry, list):
                        entry_values = {e.lower(): ini_data[tag].get(e, "") for e in entry}
                        category_result[sub_category] = entry_values
                    else:
                        entry_value = ini_data[tag].get(entry, "")
                        category_result[sub_category] = entry_value
                else:
                    category_result[sub_category] = True
                return  # Sort de la boucle dès qu'une condition est remplie




def process_conditions(ini_data, sub_details, tag, sub_category_result, index, only_one):
    """
    Processes conditions for a sub-category and updates the result.
    """
    entry = sub_details.get("entry")
    entries = sub_details.get("entries", {})
    return_value = sub_details.get("return_value", False)

    conditions_met = True
    if entries:
        for k, v in entries.items():
            possible_values = v.split('|')
            ini_value = ini_data[tag].get(k, None)
            if not any(val.strip() == ini_value for val in possible_values):
                conditions_met = False
                break

    if conditions_met:
        if return_value and entry:
            series_result = {e.lower(): ini_data[tag].get(e, "") for e in entry} if isinstance(entry, list) else ini_data[tag].get(entry, "")
            sub_category_result[str(index)] = series_result
        else:
            sub_category_result[str(index)] = True
        return True
    return False



def check_entries(ini_data, tags, entries=None):
    """
    Checks the entries for the specified tags.

    Args:
    ini_data (dict): Dictionary containing INI file data.
    tags (list): List of tags to check.
    entries (dict): Specific entries to check for each tag.

    Returns:
    bool: True if all specified entries match, False otherwise.
    """
    print(f"Checking entries for tags: {tags}, with specific entries: {entries}")
    if not entries:
        # If no entries are specified, just check for the presence of tags
        for tag in tags:
            tag = tag.strip("[]")
            if tag in ini_data:
                print(f"Tag '{tag}' found without specific entries.")
                return True
        print("No matching tag found without specific entries.")
        return False

    # If entries are specified, check for the presence of the tag and matching of entries
    for tag in tags:
        tag = tag.strip("[]")
        if tag not in ini_data:
            print(f"Tag '{tag}' not found.")
            continue

        data = ini_data[tag]
        all_entries_match = True
        for key, value in entries.items():
            if value.endswith("!"):
                # For values ending with "!", check for inclusion
                search_value = value[:-1] # Remove "!" from the value
                if key not in data or search_value not in data[key]:
                    print(f"Entry '{key}' does not contain '{search_value}' for tag '{tag}'.")
                    all_entries_match = False
                    break
            elif '|' in value:
                # Split the value by '|' and check if any of the values is present
                possible_values = value.split('|')
                if key not in data or not any(val.strip() in data[key] for val in possible_values):
                    print(f"None of the possible values for '{key}' match for tag '{tag}'.")
                    all_entries_match = False
                    break
            else:
                # Exact match for other values
                if key not in data or data[key] != value:
                    print(f"Entry '{key}' does not match or is absent for tag '{tag}'.")
                    all_entries_match = False
                    break

        if all_entries_match:
            print(f"All specified entries match for tag '{tag}'.")
            return True

    print("No match for the specified tags and entries.")
    return False


if __name__ == '__main__':
    # Paths for Cars and Tracks
    # ini_file_path = './cars/ext_config.ini'
    # json_file_path = './cars/car_csp.json'
    # For Tracks
    ini_file_path = './tracks/ext_config.ini'
    json_file_path = './tracks/track_csp.json'

    # Read and process the data
    ini_data = read_ini_file(ini_file_path)
    json_template = read_json_file(json_file_path)
    result = process_data(ini_data, json_template)

    # Print the results
    print(json.dumps(result, indent=4))
