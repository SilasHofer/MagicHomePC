import csv

# Save a name and IP address to a CSV file
def save_to_csv(name, ip, filename="devices.csv"):
    # Open in append mode and write as a new row
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([name, ip])
    print(f"Saved {name} with IP {ip} to {filename}\n")

# Read all entries from the CSV file
def read_from_csv(filename="devices.csv"):
    entries = []
    try:
        with open(filename, "r") as file:
            reader = csv.reader(file)
            for row in reader:
                entries.append((row[0], row[1]))
    except FileNotFoundError:
        return []  # Return empty list if file does not exist
    return entries
