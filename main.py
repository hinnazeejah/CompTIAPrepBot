import discord
import os
import requests
import json
from dotenv import load_dotenv
from discord.ext import commands
from discord import Embed

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENROUTER_KEY = os.getenv('OPENROUTER_API_KEY')

def getResponse(model, query):
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
        },
        data=json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": query}],
        })
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"API call failed with status code {response.status_code}")
        return None


client = commands.Bot(command_prefix='!', intents=discord.Intents.all())


async def quiz(interaction, test):
    await interaction.response.defer(ephemeral=False)

    react = ["🇦","🇧","🇨","🇩"]

    def check(reaction, user):
        return user == interaction.user and str(reaction.emoji) in react

    response = getResponse("google/gemma-7b-it:free", f"""I am currently studying to get my CompTIA {test}. 
    I want you to provide me with a practice A, B, C, D-style multiple choice question to prepare me for the {test} exam. 
    Base the question on the {test} exam objectives. There should be one clear answer. 
    Only give me questions that are related to the {test} exam.
    Only return the question and the answer choices. I don't need any introductions, instructions, or explanations, just get to the point.
    Don't tell me what the correct answer is. Also don't repeat the answer choices.
    Your response should always be in this format:
    ### Question:
    ### Answer Choices:
    A.
    B.
    C.
    D.""")

    response = response['choices'][0]['message']['content']

    try:
        mes = await interaction.channel.send(response)
        for tmp in react:
            await mes.add_reaction(tmp)
    except Exception as e:
        await interaction.followup.send("An error occurred")

    try:

        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)

        response2 = getResponse("google/gemma-7b-it:free", f"""Based on the {test} exam objectives, tell me if my answer ({reaction}) is CORRECT or INCORRECT given the following question: [{response}]. 
        Explain why my choice is correct or incorrect and if it is incorrect, tell me what the actual correct answer is and explain why. 
        Don't explain any of the other choices.
        Your response should always be in this format:
        ### Your Answer: {reaction}
        ### Correct Answer: (a, b, c, or d)
        ### Explanation:""")
        response2 = response2['choices'][0]['message']['content']

        await interaction.followup.send(response2)

    except TimeoutError:

        response2 = getResponse("google/gemma-7b-it:free", f"""Based on the {test} exam objectives, tell me the correct answer given the following question: [{response}]. 
        Explain why that answer is correct.
        Don't explain any of the other choices.
        Your response should always be in this format:
        ### Correct Answer: (a, b, c, or d)
        ### Explanation:""")
        response2 = response2['choices'][0]['message']['content']

        await interaction.followup.send("Your time has run out!\n" + response2)

    except Exception as e:
        await interaction.followup.send("An error occurred")


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="Helping students prepare for their CompTIA exams!"))
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    print("Ready to prep for you certifications!")

@client.tree.command(name="sec_plus_prep", description="Learn about specific Security+ topics.")
async def security_learn(interaction: discord.Interaction, topic: str):

    await interaction.response.defer(ephemeral=False)

    response = getResponse("gryphe/mythomist-7b:free", f"""I am currently studying to get my CompTIA Security+. I want you to act as if you are my tutor preparing me for the exam. I am going to ask you a question about {topic}. I want your answers to include a few things: the general overview of the concept and what I might need to know about it for the Security+ Exam. Answer all of my questions in this format, until I say otherwise. 
                           
    Question: What is {topic}?""")

    response = response['choices'][0]['message']['content']
    try:
       
        await interaction.followup.send(response)
    except Exception as e:
        await interaction.followup.send("An error occurred")

@client.tree.command(name="sec_plus_quiz", description="Generate a practice multiple choice question to prepare for the Security+!")
async def security_quiz(interaction: discord.Interaction):
    await quiz(interaction, "Security+")

@client.tree.command(name="a_plus_quiz", description="Generate a practice multiple choice question to prepare for the A+!")
async def security_quiz(interaction: discord.Interaction):
    await quiz(interaction, "A+")

@client.tree.command(name="net_plus_quiz", description="Generate a practice multiple choice question to prepare for the Network+!")
async def security_quiz(interaction: discord.Interaction):
    await quiz(interaction, "Network+")


client.run(DISCORD_TOKEN)
