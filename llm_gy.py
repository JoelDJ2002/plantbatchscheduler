import json
import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

def analyze_scheduling_results_data(data, groq_api_key=None):
    """
    Analyze production scheduling simulation results using Groq LLM.
    
    Args:
        data: Simulation results data (dict or JSON string)
        groq_api_key: Groq API key (if None, reads from GROQ_API_KEY env var)
    
    Returns:
        str: Analysis text from the LLM
    """
    
    # Initialize Groq client
    if groq_api_key is None:
        groq_api_key = os.environ.get("GROQ_API_KEY")
    
    if not groq_api_key:
        raise ValueError("Groq API key must be provided or set in GROQ_API_KEY environment variable. Create a .env file with GROQ_API_KEY=your_key")
    
    client = Groq(api_key=groq_api_key)
    
    # Parse data if it's a string
    if isinstance(data, str):
        data = json.loads(data)
    
    # Create analysis prompt
    prompt = f"""You are a production scheduling and operations research expert. Analyze the following manufacturing plant simulation results and provide actionable recommendations.

        SIMULATION DATA:
        {json.dumps(data, indent=2)}

        Provide a comprehensive analysis covering:

        1. **Algorithm Performance Comparison**: Which scheduling algorithm performed best and why? Compare makespan, tardiness, and late orders.

        2. **Bottleneck Analysis**: Identify the critical bottlenecks in the system. What equipment is constraining throughput?

        3. **Capacity Utilization Issues**: Analyze the utilization rates. What do low utilization rates indicate about the plant configuration?

        4. **Order Fulfillment Problems**: Which orders are consistently late? What patterns do you see in tardiness across algorithms?

        5. **Specific Recommendations**: Provide 3-5 concrete, prioritized recommendations to improve this operation. Consider:
        - Equipment reallocation or investment
        - Scheduling algorithm selection
        - Process improvements
        - Order management strategies

        Be specific with numbers and reference the actual data. Prioritize recommendations by impact and implementation difficulty."""

    # Call Groq API
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an expert in production scheduling, operations research, and manufacturing optimization with 20+ years of experience."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        temperature=0.3,
        top_p=0.9
    )
    
    analysis = chat_completion.choices[0].message.content
    
    return analysis


def analyze_scheduling_results(json_file_path, groq_api_key=None):
    """
    Analyze production scheduling simulation results using Groq LLM.
    
    Args:
        json_file_path: Path to the simulation results JSON file
        groq_api_key: Groq API key (if None, reads from GROQ_API_KEY env var)
    """
    
    # Initialize Groq client
    if groq_api_key is None:
        groq_api_key = os.environ.get("GROQ_API_KEY")
    
    if not groq_api_key:
        raise ValueError("Groq API key must be provided or set in GROQ_API_KEY environment variable. Create a .env file with GROQ_API_KEY=your_key")
    
    client = Groq(api_key=groq_api_key)
    
    # Load simulation results
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    # Create analysis prompt
    prompt = f"""You are a production scheduling and operations research expert. Analyze the following manufacturing plant simulation results and provide actionable recommendations.

        SIMULATION DATA:
        {json.dumps(data, indent=2)}

        Provide a comprehensive analysis covering:

        1. **Algorithm Performance Comparison**: Which scheduling algorithm performed best and why? Compare makespan, tardiness, and late orders.

        2. **Bottleneck Analysis**: Identify the critical bottlenecks in the system. What equipment is constraining throughput?

        3. **Capacity Utilization Issues**: Analyze the utilization rates. What do low utilization rates indicate about the plant configuration?

        4. **Order Fulfillment Problems**: Which orders are consistently late? What patterns do you see in tardiness across algorithms?

        5. **Specific Recommendations**: Provide 3-5 concrete, prioritized recommendations to improve this operation. Consider:
        - Equipment reallocation or investment
        - Scheduling algorithm selection
        - Process improvements
        - Order management strategies

        Be specific with numbers and reference the actual data. Prioritize recommendations by impact and implementation difficulty."""

    # Call Groq API
    print("Analyzing scheduling results with Groq LLM...\n")
    print("=" * 80)
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an expert in production scheduling, operations research, and manufacturing optimization with 20+ years of experience."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="meta-llama/llama-4-maverick-17b-128e-instruct",  # Fast and capable model
        temperature=0.3,  # Lower temperature for more focused, analytical responses
        # max_completion_tokens=1024,
        top_p=0.9
    )
    
    analysis = chat_completion.choices[0].message.content
    
    print(analysis)
    print("\n" + "=" * 80)
    
    # Print metadata
    print(f"\nModel: {chat_completion.model}")
    print(f"Tokens used: {chat_completion.usage.total_tokens}")
    print(f"Prompt tokens: {chat_completion.usage.prompt_tokens}")
    print(f"Completion tokens: {chat_completion.usage.completion_tokens}")
    
    return analysis


def interactive_analysis(json_file_path, groq_api_key=None):
    """
    Interactive mode: Ask follow-up questions about the scheduling results.
    
    Args:
        json_file_path: Path to the simulation results JSON file
        groq_api_key: Groq API key
    """
    
    if groq_api_key is None:
        groq_api_key = os.environ.get("GROQ_API_KEY")
    
    client = Groq(api_key=groq_api_key)
    
    # Load data
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    conversation_history = [
        {
            "role": "system",
            "content": "You are an expert in production scheduling and manufacturing optimization. You have access to simulation results data."
        },
        {
            "role": "user",
            "content": f"Here's the production scheduling simulation data I want to discuss:\n\n{json.dumps(data, indent=2)}\n\nI'll ask you questions about it."
        },
        {
            "role": "assistant",
            "content": "I've analyzed your production scheduling simulation data. I can see results for three algorithms (FIFO, EDD, Critical Ratio) across multiple orders and equipment. What would you like to know?"
        }
    ]
    
    print("Interactive Analysis Mode - Type 'quit' to exit\n")
    print("=" * 80)
    
    while True:
        user_question = input("\nYour question: ").strip()
        
        if user_question.lower() in ['quit', 'exit', 'q']:
            break
        
        if not user_question:
            continue
        
        conversation_history.append({
            "role": "user",
            "content": user_question
        })
        
        response = client.chat.completions.create(
            messages=conversation_history,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1500
        )
        
        assistant_message = response.choices[0].message.content
        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        print(f"\nAssistant: {assistant_message}")


# Example usage
if __name__ == "__main__":
    # Set your Groq API key
    # Option 1: Set as environment variable
    # export GROQ_API_KEY='your_key_here'
    
    # Option 2: Pass directly (not recommended for production)
    # API_KEY = "your_groq_api_key_here"
    
    json_file = "simulation_results.json"
    
    # Run initial analysis
    print("INITIAL ANALYSIS")
    print("=" * 80 + "\n")
    analysis = analyze_scheduling_results(json_file)
    
    # Optionally start interactive mode
    print("\n\n" + "=" * 80)
    response = input("\nWould you like to ask follow-up questions? (y/n): ")
    if response.lower() == 'y':
        interactive_analysis(json_file)