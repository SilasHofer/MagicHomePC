import csv

# Save a name and IP address to a CSV file
def save_to_csv(name, ip, filename="devices.csv"):
    # Open in append mode and write as a new row
    with open(filename, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([name, ip])
    return True

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

def remove_from_csv(ip,filename="devices.csv"):
    devices = read_from_csv()
    devices = [row for row in devices if row[1] != ip]
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(devices)
    return True
