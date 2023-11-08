import json

class Data():
    def __init__(self, json_file):
        # Constructor for the Data class. Initializes the object with a JSON file.
        self.json_file = json_file

        # Opens and reads the JSON file, storing its contents in the 'get' attribute.
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        self.get = data

    def save(self, data1, data2=None):
        # Appends 'data1' to the 'get' attribute, and if 'data2' is provided, appends it as well.
        self.get.append(data1)
        if not data2 == None:
            self.get.append(data2)
        
        # Writes the updated 'get' attribute back to the JSON file, overwriting its previous contents.
        with open(self.json_file, 'w', encoding='utf-8') as file:
            json.dump(self.get, file, indent=4)

    def remove(self, data):
        # Removes 'data' from the 'get' attribute.
        self.get.remove(data)
        
        # Writes the updated 'get' attribute back to the JSON file, overwriting its previous contents.
        with open(self.json_file, 'w', encoding='utf-8') as file:
            json.dump(self.get, file, indent=4)
    
    def save_and_retrieve(self, data1, data2=None):
        # Appends 'data1' to the 'get' attribute, and if 'data2' is provided, appends it as well.
        self.get.append(data1)
        if not data2 == None:
            self.get.append(data2)
        
        # Writes the updated 'get' attribute back to the JSON file, overwriting its previous contents.
        with open(self.json_file, 'w', encoding='utf-8') as file:
            json.dump(self.get, file, indent=4)
        
        # Reads the JSON file and returns its contents after the updates.
        with open(self.json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    
    def is_empty(self) -> bool:
        # Checks if the 'get' attribute is an empty list and returns True if it is, otherwise returns False.
        if self.get == []:
             return True
        else:
             return False
