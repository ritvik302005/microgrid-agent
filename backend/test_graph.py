from dotenv import load_dotenv
load_dotenv()

from graph import graph

result = graph.invoke({})

print("Decision:", result["decision"])
print("Reasoning:", result["reasoning"])
print("Alerts:", result["alerts"])
print("Report:", result["report"])