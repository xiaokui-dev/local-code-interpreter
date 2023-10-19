from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage


system_message = SystemMessage(
    content="""
You are using an AI Assistant capable of tasks related to data science, data analysis, data visualization, and file manipulation. Capabilities include:

- Image Manipulation: Zoom, crop, color grade, enhance resolution, format conversion.
- QR Code Generation: Create QR codes.
- Project Management: Generate Gantt charts, map project steps.
- Study Scheduling: Design optimized exam study schedules.
- File Conversion: Convert files, e.g., PDF to text, video to audio.
- Mathematical Computation: Solve equations, produce graphs.
- Document Analysis: Summarize, extract information from large documents.
- Data Visualization: Analyze datasets, identify trends, create graphs.
- Geolocation Visualization: Show maps to visualize specific trends or occurrences.
- Code Analysis and Creation: Critique and generate code.

The Assistant operates within a sandboxed Jupyter kernel environment. Pre-installed Python packages include numpy, pandas, matplotlib, seaborn, scikit-learn, yfinance, scipy, statsmodels, sympy, bokeh, plotly, dash, and networkx. Other packages will be installed as required.

To use, input your task-specific code. Review and retry code in case of error. After two unsuccessful attempts, an error message will be returned.

The Assistant is designed for specific tasks and may not function as expected if used incorrectly.
"""
)


determine_modifications_prompt = PromptTemplate(
    input_variables=["code"],
    template="The user will input some code and you need to determine "
    "if the code makes any changes to the file system. \n"
    "With changes it means creating new files or modifying existing ones.\n"
    "Format your answer as JSON inside a codeblock with a "
    "list of filenames that are modified by the code.\n"
    "If the code does not make any changes to the file system, "
    "return an empty list.\n\n"
    "Determine modifications:\n"
    "```python\n"
    "import matplotlib.pyplot as plt\n"
    "import numpy as np\n\n"
    "t = np.arange(0.0, 4.0*np.pi, 0.1)\n\n"
    "s = np.sin(t)\n\n"
    "fig, ax = plt.subplots()\n\n"
    "ax.plot(t, s)\n\n"
    'ax.set(xlabel="time (s)", ylabel="sin(t)",\n'
    '   title="Simple Sin Wave")\n'
    "ax.grid()\n\n"
    'plt.savefig("sin_wave.png")\n'
    "```\n\n"
    "Answer:\n"
    "```json\n"
    "{{\n"
    '  "modifications": ["sin_wave.png"]\n'
    "}}\n"
    "```\n\n"
    "Determine modifications:\n"
    "```python\n"
    "import matplotlib.pyplot as plt\n"
    "import numpy as np\n\n"
    "x = np.linspace(0, 10, 100)\n"
    "y = x**2\n\n"
    "plt.figure(figsize=(8, 6))\n"
    "plt.plot(x, y)\n"
    'plt.title("Simple Quadratic Function")\n'
    'plt.xlabel("x")\n'
    'plt.ylabel("y = x^2")\n'
    "plt.grid(True)\n"
    "plt.show()\n"
    "```\n\n"
    "Answer:\n"
    "```json\n"
    "{{\n"
    '  "modifications": []\n'
    "}}\n"
    "```\n\n"
    "Determine modifications:\n"
    "```python\n"
    "{code}\n"
    "```\n\n"
    "Answer:\n"
    "```json\n",
)

remove_dl_link_prompt = ChatPromptTemplate(
    input_variables=["input_response"],
    messages=[
        SystemMessage(
            content="The user will send you a response and you need "
            "to remove the download link from it.\n"
            "Reformat the remaining message so no whitespace "
            "or half sentences are still there.\n"
            "If the response does not contain a download link, "
            "return the response as is.\n"
        ),
        HumanMessage(
            content="The dataset has been successfully converted to CSV format. "
            "You can download the converted file [here](sandbox:/Iris.csv)."
        ),  # noqa: E501
        AIMessage(content="The dataset has been successfully converted to CSV format."),
        HumanMessagePromptTemplate.from_template("{input_response}"),
    ],
)
