import json

class Storage:

    @staticmethod
    def save_user(user, filename):

        data = {
            "name": user.name,
            "age": user.age,
            "weight": user.weight,
            "height": user.height
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load_user(filename):

        with open(filename) as f:
            return json.load(f)