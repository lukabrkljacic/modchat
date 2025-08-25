# mod-agent 
The LLM decomposition function found in the backend is implemented as an Agent conforming to the A2A protocol. 
## Server
- Create a .env file using the env.sample file to start with and fill in the values for your environment. 
- Use this Dockerfile
```
FROM python:3.11 AS prod
RUN apt-get update -y && \
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin/:$PATH"
COPY ./src /src
WORKDIR /src
RUN uv pip install --no-cache-dir -r requirements.txt --system
ENV FLASK_APP=/src/server.py
EXPOSE 9999
WORKDIR /src
ENTRYPOINT [ "python" ]
CMD [ "server.py" ]
```
```
docker build . -t mod-agent
docker run -p 9999:9999 mod-agent
```
From a browser on the host go to http://modchat.localhost/agent/info to verify that the server is up and reponding. 

### Sample

```
Discovered Agent: DecomposeAgent - Agent that decomposes a solution into components
Sending task 934d16d8-4c65-4e5a-8f02-39eedcff369a to agent with message: 'Why is the sky blue?'

== Components ==
{'Explanation of Phenomenon': 'The sky is blue because of a phenomenon called Rayleigh scattering.'}
{'Interaction with Atmosphere': "When sunlight enters Earth's atmosphere, it collides with molecules and small particles."}
{'Reason for Blue Light Scattering': 'Blue light waves are scattered in all directions more than other colors because they have shorter wavelengths.'}
{'Resulting Perception': 'This scattering causes the sky to appear blue to our eyes during the day.'}
```
```
== outputStructure ==
- Explanation of Phenomenon
- Interaction with Atmosphere
- Reason for Blue Light Scattering
- Resulting Perception
```
