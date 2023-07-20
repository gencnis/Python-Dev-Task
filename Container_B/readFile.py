def read_country_data(file_path):
    country_data = {}
    with open(file_path, "r") as file:
        for line in file:
            code, name = line.strip().split(": ")
            # Remove double quotes from the name
            name = name.strip('"')
            country_data[code.strip('"')] = name
    return country_data