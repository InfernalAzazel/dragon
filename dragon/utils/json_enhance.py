

class JsonEnhance:
    def __init__(self, list_json):
        self.list_json = list_json

    def findOne(self, key: str, value):
        for lj in self.list_json:
            for k, v in lj.items():
                if k == key and v == value:
                    return lj
        return {}