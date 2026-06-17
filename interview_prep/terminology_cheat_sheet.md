# Tech Terms & Function Cheat Sheet

This is your quick glossary. It explains what the key terms mean in simple language and breaks down the exact functions used in this project with their one-line job.

---

## 1. Core Frameworks (What they are)

* **State Machine (Stateflow)**: "It's just a workflow diagram turned into code. You define steps (nodes) and rules (edges) to transition between them. The state travels along the path and updates at each step."
* **Pydantic**: "A library that validates data. It acts like a bouncer at the API door. If the input data doesn't match the schema we defined, Pydantic blocks it before it runs any backend code."
* **FastAPI**: "A very fast, modern python framework to build APIs. It works natively with Pydantic and supports async requests out of the box."
* **LangChain**: "A wrapper library that makes it easy to talk to different AI models (like OpenAI or Gemini) using prompt templates, without writing custom API requests."
* **LangGraph**: "A library built on top of LangChain that lets us build complex AI agents as state machines. It handles the routing, memory, and steps of the AI flow."
* **Pytest**: "A tool we use to run our automated tests. It runs our code with test queries and verifies if it returns correct status codes and JSON outputs."
* **Asyncio (Asynchronous Programming)**: "A way of writing python code that doesn't block. While the code is waiting for a response from the LLM API, it can handle other incoming requests at the same time."

---

## 2. Pydantic Functions used in this Project

* **`BaseModel`**: "The parent class we inherit from to create validation schemas (like `QueryRequest`)."
* **`Field(...)`**: "Defines validation settings for schema variables (like forcing a query to be at least 1 character long via `min_length=1`)."

---

## 3. FastAPI Functions used in this Project

* **`FastAPI()`**: "Creates the main web server app instance."
* **`@app.exception_handler(...)`**: "A decorator that catches errors (like validation crashes) globally so we can return custom JSON instead of raw python tracebacks."
* **`JSONResponse()`**: "Formulates and returns data as a formatted JSON response with a specific HTTP status code (like 422 or 500)."

---

## 4. LangChain Functions used in this Project

* **`ChatPromptTemplate.from_messages(...)`**: "Formats our text prompt template, feeding the user's query into the system instructions before sending it to the model."
* **`StrOutputParser()`**: "Parses the LLM's raw response object and extracts just the output text string."
* **`llm.with_structured_output(...)`**: "Forces the LLM to format its response strictly as a JSON object matching our Pydantic schema (`GuardrailOutput`)."
* **`RunnableLambda(...)`**: "Converts a normal Python function into a LangChain runnable step so it can be combined easily with other chains."

---

## 5. LangGraph Functions used in this Project

* **`StateGraph(AgentState)`**: "Creates the blueprint of our state machine, initialized with the variables it needs to track."
* **`add_node(name, function)`**: "Registers a step in the workflow (like adding `guardrail` or `respond` steps)."
* **`set_entry_point(name)`**: "Sets which node the state machine should start running from (our entry point is `guardrail`)."
* **`add_conditional_edges(...)`**: "Branches the path based on a router function (determines if we go to `respond` or stop early at `END`)."
* **`add_edge(from_node, to_node)`**: "Creates a straight-line connection between two steps (connecting `respond` directly to `END`)."
* **`compile()`**: "Builds and locks the graph structure, turning it into an executable app."
* **`invoke(input_data)`**: "Starts executing the compiled graph by feeding it the initial inputs (like the user query)."

---

## 6. Asyncio Keywords used in this Project

* **`async def`**: "Tells Python that this function runs asynchronously, meaning it won't freeze the backend server while waiting on I/O."
* **`await`**: "Pauses the async function to wait for a task to finish (like waiting for the LLM output), allowing the server to handle other client requests in the meantime."
