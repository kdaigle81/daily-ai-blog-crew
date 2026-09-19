"""
MVP Daily AI Tools Blog Agent Crew
Researcher -> Writer -> Publisher
Free start: DuckDuckGo search + OpenAI/Groq + WP REST
Run: python main.py
Cron daily. No money needed to start.
"""
import os
from crewai import Agent, Task, Crew, Process
from langchain_community.tools import DuckDuckGoSearchRun
import requests
from datetime import datetime

search_tool = DuckDuckGoSearchRun()

researcher = Agent(
    role="AI Tools Researcher",
    goal="Find 3 newest AI video or SEO tools this week with prices",
    backstory="You hunt fresh AI launches daily. Accurate, short summaries.",
    tools=[search_tool],
    verbose=True,
    allow_delegation=False,
)

writer = Agent(
    role="Blog Writer",
    goal="Write 500-word catchy professional-funny post from research",
    backstory="You write like a smart friend. Hook titles. SEO light.",
    verbose=True,
    allow_delegation=False,
)

publisher = Agent(
    role="WordPress Publisher",
    goal="Post the article as draft or live via WP API",
    backstory="You push content live without mistakes.",
    verbose=True,
    allow_delegation=False,
)

research_task = Task(
    description="Search news for 3 new AI video tools or SEO software released this week. Summarize name, what it does, price, link.",
    expected_output="Bullet list of 3 tools with price and one-line desc.",
    agent=researcher,
)

write_task = Task(
    description="Write a 500-word blog post. Catchy title. Professional but funny voice. Intro, 3 tool sections, conclusion with CTA.",
    expected_output="Full markdown blog post ready to publish. Title on first line.",
    agent=writer,
    context=[research_task],
)

def publish_to_wp(content: str):
    url = os.getenv("WP_URL", "https://yoursite.com/wp-json/wp/v2/posts")
    user = os.getenv("WP_USER")
    app_pass = os.getenv("WP_APP_PASSWORD")
    if not user or not app_pass:
        print("Set WP_USER and WP_APP_PASSWORD. Saving locally instead.")
        with open("draft.md", "w") as f:
            f.write(content)
        return "Saved draft.md"
    title = content.split("\n")[0].replace("#", "").strip()
    body = "\n".join(content.split("\n")[1:])
    r = requests.post(
        url,
        auth=(user, app_pass),
        json={"title": title, "content": body, "status": "draft"},
    )
    return r.json() if r.ok else r.text

publish_task = Task(
    description="Take the written post and publish it to WordPress as draft.",
    expected_output="Confirmation of post created with ID or local file.",
    agent=publisher,
    context=[write_task],
)

crew = Crew(
    agents=[researcher, writer, publisher],
    tasks=[research_task, write_task, publish_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print("Running daily crew", datetime.now())
    result = crew.kickoff()
    print(result)
    if "draft.md" not in str(result):
        publish_to_wp(str(result))
