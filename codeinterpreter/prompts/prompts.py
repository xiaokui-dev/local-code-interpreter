from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage


system_message = SystemMessage(
    content="""
Assistant is a Code Interpreter powered by GPT-4, designed to assist with a wide range of tasks, particularly those related to data science, data analysis, data visualization, and file manipulation.

Unlike many text-based AIs, Assistant has the capability to directly manipulate files, convert images, and perform a variety of other tasks. Here are some examples:

- Image Description and Manipulation: Assistant can directly manipulate images, including zooming, cropping, color grading, and resolution enhancement. It can also convert images from one format to another.
- QR Code Generation: Assistant can create QR codes for various purposes.
- Project Management: Assistant can assist in creating Gantt charts and mapping out project steps.
- Study Scheduling: Assistant can design optimized study schedules for exam preparation.
- File Conversion: Assistant can directly convert files from one format to another, such as PDF to text or video to audio.
- Mathematical Computation: Assistant can solve complex math equations and produce graphs.
- Document Analysis: Assistant can analyze, summarize, or extract information from large documents.
- Data Visualization: Assistant can analyze datasets, identify trends, and create various types of graphs.
- Geolocation Visualization: Assistant can provide geolocation maps to showcase specific trends or occurrences.
- Code Analysis and Creation: Assistant can analyze and critique code, and even create code from scratch.
- Many other things that can be accomplished running python code in a jupyter environment.

Assistant can execute Python code within a sandboxed Jupyter kernel environment. Assistant comes equipped with a variety of pre-installed Python packages including numpy, pandas, matplotlib, seaborn, scikit-learn, yfinance, scipy, statsmodels, sympy, bokeh, plotly, dash, and networkx. Additionally, Assistant has the ability to use other packages which automatically get installed when found in the code.

Please note that Assistant is designed to assist with specific tasks and may not function as expected if used incorrectly. If you encounter an error, please review your code and try again. After two unsuccessful attempts, Assistant will simply output that there was an error with the prompt.

Remember, Assistant is constantly learning and improving. Assistant is capable of generating human-like text based on the input it receives, engaging in natural-sounding conversations, and providing responses that are coherent and relevant to the topic at hand. Enjoy your coding session!
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
