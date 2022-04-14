import json 

class JsonHandler:

    def read(self,file):
        with open(file, "rb") as outfile:
            content = json.load(outfile)
            return content

    def write(self,file):
        pass
