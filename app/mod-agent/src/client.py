import requests
import uuid
import a2a.types
import json
import argparse

def processResponse(task_response: dict):
    task = a2a.types.Task.model_validate_json(json.dumps(task_response))
    if task.artifacts != None:
        for artifact in task.artifacts:
            for part in artifact.parts:
                data = part.root
                print("== Components ==")
                for component in data.data.get("components", []):
                    print(component)
                print("== outputStructure ==")
                for output_structure in data.data.get("outputStructure", []):
                    print(output_structure)
                output_type = data.data.get("outputType", "")
                print("==")
                print(f"outputType: {output_type}")

def main(agent_base_url: str, user_text: str):
    # 1. Discover the agent by fetching its Agent Card
    agent_card_url = f"{agent_base_url}/.well-known/agent.json"
    response = requests.get(agent_card_url)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to get agent card: {response.status_code}")
    agent_card = response.json()
    print("Discovered Agent:", agent_card["name"], "-", agent_card.get("description", ""))
    
    # 2. Prepare a task request for the agent
    task_id = str(uuid.uuid4())  # generate a random unique task ID
    task_payload = {
        "id": task_id,
        "message": {
            "role": "user",
            "parts": [
                {"text": user_text}
            ]
        }
    }
    print(f"Sending task {task_id} to agent with message: '{user_text}'")
    
    # 3. Send the task to the agent's tasks/send endpoint
    tasks_send_url = f"{agent_base_url}/tasks/send"
    result = requests.post(tasks_send_url, json=task_payload)
    if result.status_code != 200:
        raise RuntimeError(f"Task request failed: {result.status_code}, {result.text}")
    task_response = result.json()
    # 4. Process the agent's response
    processResponse(task_response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="command-line parser")
    parser.add_argument("-url", "--agent-base-url", type=str, default="http://localhost:9999", help="The base url for the agent")
    parser.add_argument("-q", "--question", type=str, default="Why is the sky blue?", help="A request to send to the agent")
    args = parser.parse_args()
    main(args.agent_base_url, args.question)