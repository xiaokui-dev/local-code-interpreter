from codeinterpreter.localbox import (LocalBox, upload, list_files,download)
import requests


codebox = LocalBox()
codebox.start()
csv_bytes = requests.get(
        "https://archive.ics.uci.edu/" "ml/machine-learning-databases/iris/iris.data"
    ).content
upload("iris.csv", csv_bytes)

codebox.install("pandas")
codebox.install("openpyxl")

output1 = codebox.run(
    "import os\n\n"
    "print(os.getcwd())\n\n")

# convert dataset csv to excel
output = codebox.run(
    "import pandas as pd\n\n"
    "df = pd.read_csv('iris.csv', header=None)\n\n"
    "df.to_excel('iris.xlsx', index=False)\n"
    "'iris.xlsx'"
)

# check output type
if output.type == "image/png":
    print("This should not happen")
elif output.type == "error":
    print("Error: ", output.content)
else:
    for file in list_files():
        print("File: ", file.name)
        print("Content is None: ", file.content is None)
        content = download(file.name)
        print("Content: ", content)