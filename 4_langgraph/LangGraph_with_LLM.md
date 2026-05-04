# Adding an LLM to LangGraph

In the second half of `1_lab1.ipynb`, the notebook demonstrates the exact same 5-step process, but with one crucial difference: we replace our manual Python string-generator with a real Large Language Model (LLM).

Here is a breakdown of how the architecture adapts to use an LLM:

---

### Step 1: Define the State
```python
class State(BaseModel):
    messages: Annotated[list, add_messages]
```
The **State** serves as the graph's memory. Here, we define a Pydantic `BaseModel` with a single field called `messages`. The `Annotated[list, add_messages]` tells LangGraph that this field is a list, and it should use the `add_messages` reducer function. This means whenever a node outputs a new message, LangGraph will automatically append it to the existing list rather than overwriting it, preserving our conversation history.

### Step 2: Initialize the Graph Builder
```python
graph_builder = StateGraph(State)
```
We initialize the graph by passing it our `State` schema. This prepares the LangGraph engine, telling it exactly what data structure will be flowing between the nodes we are about to create.

### Step 3: The New Chatbot Node
```python
llm = ChatOpenAI(model="gpt-4o-mini")

def chatbot_node(old_state: State) -> State:
    # Pass the ENTIRE conversation history to the LLM
    response = llm.invoke(old_state.messages)
    
    # Return the LLM's response packaged in our State object
    new_state = State(messages=[response])
    return new_state

graph_builder.add_node("chatbot", chatbot_node)
```
This is where the magic happens. 
* We initialize our LLM connection (`ChatOpenAI`).
* Instead of picking random nouns and adjectives, our node takes `old_state.messages` (which includes the system prompt, history, and the user's latest message) and passes it directly into the LLM via `llm.invoke()`.
* The LLM returns an `AIMessage` object. 
* We wrap that `AIMessage` inside our `State` and return it. LangGraph's `add_messages` reducer automatically appends it to the history.

### Steps 4 & 5: Edges and Compilation
```python
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

graph = graph_builder.compile()
```
The flow is identical to the first example: `START` $\rightarrow$ `chatbot` node $\rightarrow$ `END`. 

### The Big Picture
The notebook is showing you a profound concept: **wrapping an LLM in a Node.**

While a `START -> chatbot -> END` graph might seem like overkill for a simple chat application, this structure becomes incredibly powerful when things get complex. Because your LLM is just a "Node" in a graph, in the future you can easily draw edges to *other* nodes:
* `chatbot` $\rightarrow$ `tool_executor_node`
* `chatbot` $\rightarrow$ `evaluator_node`
* `human_review_node` $\rightarrow$ `chatbot`

By putting the LLM into this State/Node framework, you've laid the foundation for building multi-step, agentic workflows.
