from langchain_core.runnables import RunnableLambda, RunnableSequence, RunnableParallel, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from operator import itemgetter
import os

# Ensure your OPENAI_API_KEY is set in your environment variables.

def basic_pipe_example():
    """
    Example 1: The '|' operator creates a RunnableSequence automatically.
    This is the most common way to build chains.
    """
    print("--- Example 1: Basic '|' Operator ---")
    
    prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
    model = ChatOpenAI(model="gpt-4o-mini")
    parser = StrOutputParser()

    # The '|' operator compiles these into a RunnableSequence
    chain = prompt | model | parser
    
    print(f"Chain type: {type(chain)}")
    
    result = chain.invoke({"topic": "AI agents"})
    print(f"Result: {result}\n")

def explicit_sequence_example():
    """
    Example 2: Using RunnableSequence explicitly.
    This is equivalent to using the '|' operator but more verbose.
    """
    print("--- Example 2: Explicit RunnableSequence ---")
    
    prompt = ChatPromptTemplate.from_template("Translate this to Spanish: {text}")
    model = ChatOpenAI(model="gpt-4o-mini")
    parser = StrOutputParser()

    # Explicit construction
    chain = RunnableSequence(prompt, model, parser)
    
    result = chain.invoke({"text": "Hello, how are you?"})
    print(f"Result: {result}\n")

def runnable_lambda_example():
    """
    Example 3: Using RunnableLambda for custom logic.
    RunnableLambda allows you to wrap any Python function to be part of the chain.
    """
    print("--- Example 3: RunnableLambda ---")

    # A simple python function
    def length_function(text: str) -> int:
        return len(text)
    
    # A function that modifies the input
    def uppercase_input(input_dict: dict) -> dict:
        return {"topic": input_dict["topic"].upper()}

    # Wrapping them in RunnableLambda (though often implicit when creating chains)
    preprocess = RunnableLambda(uppercase_input)
    
    prompt = ChatPromptTemplate.from_template("Write a one-sentence poem about {topic}")
    model = ChatOpenAI(model="gpt-4o-mini")
    parser = StrOutputParser()
    
    # Custom post-processing step
    count_length = RunnableLambda(length_function)

    # Chain: Preprocess -> Prompt -> Model -> Parse -> Count Length
    chain = preprocess | prompt | model | parser
    
    # If we want to branch and see both text and length, we can use RunnableParallel (simulating a complex flow)
    # But for this example, let's just show the sequence flow
    result_text = (preprocess | prompt | model | parser).invoke({"topic": "ocean"})
    print(f"Poem: {result_text}")
    
    # Chain that returns length of the poem
    chain_length = chain | count_length
    result_length = chain_length.invoke({"topic": "ocean"})
    print(f"Length of poem: {result_length}\n")

def complex_pipeline_example():
    """
    Example 4: A more complex pipeline combining Sequence, Lambda, and Parallel.
    Similar to what you might use in RAG.
    """
    print("--- Example 4: Complex Pipeline ---")

    model = ChatOpenAI(model="gpt-4o-mini")
    
    # 1. First step: Generate a search query from a user question
    query_generator_prompt = ChatPromptTemplate.from_template(
        "Generate a search query for: {question}"
    )
    query_chain = query_generator_prompt | model | StrOutputParser()

    # 2. Mock Retriever: Just a lambda function that returns "fake" content based on query
    def mock_retriever(query: str):
        print(f"  (Retrieved documents for query: '{query}')")
        return f"Context about {query}: LangChain is a framework for developing applications powered by language models."

    retriever_runnable = RunnableLambda(mock_retriever)

    # 3. Main Answer Generation
    answer_prompt = ChatPromptTemplate.from_template(
        "Answer the question based on the context.\nContext: {context}\nQuestion: {question}"
    )
    answer_chain = answer_prompt | model | StrOutputParser()

    # 4. Putting it together
    # We use RunnableParallel to pass the original question along with the retrieved context
    
    # Step A: Generate Query
    # Step B: Retrieve Context using the Query
    # Step C: Pass (Question, Context) to Answer Chain

    # Method 1: Explicit steps
    full_chain = (
        RunnableParallel(
            question=itemgetter("question"), # specific key from input
            query=itemgetter("question") | query_chain # branch to generate query
        )
        | RunnableParallel(
            question=itemgetter("question"),
            context=itemgetter("query") | retriever_runnable # use query to get context
        )
        | answer_chain
    )

    result = full_chain.invoke({"question": "What is LangChain?"})
    print(f"Final Answer: {result}\n")

def runnable_assign_example():
    """
    Example 5: Using RunnablePassthrough.assign to add values to the dictionary.
    This is extremely useful when you want to calculate a value and keep the original input,
    or build up a context dictionary step-by-step without using big RunnableParallel blocks.
    """
    print("--- Example 5: RunnablePassthrough.assign ---")
    
    model = ChatOpenAI(model="gpt-4o-mini")
    
    # Let's say we have an input: {"question": "..."}
    # We want to:
    # 1. Calculate the length of the question.
    # 2. Translate the question to French.
    # 3. Use both the original question and the translation to generate a summary.
    
    def get_length(input_dict):
        return len(input_dict["question"])
    
    translation_chain = (
        ChatPromptTemplate.from_template("Translate to French: {question}") 
        | model 
        | StrOutputParser()
    )
    
    # .assign() creates a NEW key in the dictionary with the result of the runnable.
    # It passes the CURRENT state to the runnable.
    chain = (
        RunnablePassthrough.assign(length=RunnableLambda(get_length))  # Adds 'length'
        | RunnablePassthrough.assign(french_translation=translation_chain) # Adds 'french_translation'
        | RunnablePassthrough.assign(
            # We can use the NEW keys immediately in subsequent steps if we wanted to
            upper_french=lambda x: x["french_translation"].upper() 
        )
    )
    
    # Let's invoke it and see the intermediate state (which is the final result of this chain)
    result = chain.invoke({"question": "Hello world"})
    
    print("Resulting Dictionary State:")
    print(f"Original Question: {result['question']}")
    print(f"Calculated Length: {result['length']}")
    print(f"French Translation: {result['french_translation']}")
    print(f"Uppercase French: {result['upper_french']}")
    print("\n")

def runnable_pick_example():
    """
    Example 6: Using .pick() to select specific keys from the dictionary.
    This is useful for cleaning up the state or passing only specific arguments to the next step.
    """
    print("--- Example 6: Runnable .pick() ---")
    
    # Initial state
    initial_dict = {
        "question": "What is AI?",
        "context": "AI stands for Artificial Intelligence.",
        "extra_info": "This should be discarded."
    }
    
    # 1. Pick a single key
    # Returns just the value of that key
    # This is equivalent to: itemgetter("context")
    pick_one = RunnablePassthrough().pick("context")
    result_one = pick_one.invoke(initial_dict)
    print(f"Picked 'context': {result_one}")
    print(f"Type: {type(result_one)}") # Should be str
    
    # 2. Pick multiple keys
    # Returns a new dictionary with only the selected keys
    pick_multiple = RunnablePassthrough().pick(["question", "context"])
    result_multiple = pick_multiple.invoke(initial_dict)
    print(f"Picked multiple: {result_multiple}")
    
    print("\n")

if __name__ == "__main__":
    # Check for API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY environment variable to run these examples.")
    else:
        basic_pipe_example()
        explicit_sequence_example()
        runnable_lambda_example()
        complex_pipeline_example()
        runnable_assign_example()
        runnable_pick_example()
