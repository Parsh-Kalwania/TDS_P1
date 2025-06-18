import json
import os
from typing import List, Optional
from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer, util

# Load .env for OpenAI key
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()
client = OpenAI(api_key=OPENAI_API_KEY)

# Load discourse data
with open("tds_discourse_data.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

# Preprocess content
documents = []
links = []
for item in discourse_data:
    text = item["title"] + "\n" + "\n".join(item["posts"])
    documents.append(text)
    links.append(item["url"])

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")
doc_embeddings = model.encode(documents, convert_to_tensor=True)

# Request format
class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None  # not used now

# Response format
class Link(BaseModel):
    url: str
    text: str

class AnswerResponse(BaseModel):
    answer: str
    links: List[Link]

@app.post("/api/", response_model=AnswerResponse)
async def answer_question(req: QuestionRequest):
    question = req.question
    q_embedding = model.encode(question, convert_to_tensor=True)
    scores = util.cos_sim(q_embedding, doc_embeddings)[0]

    # Top 2 matches
    top_k = scores.topk(2)
    top_indices = top_k.indices.tolist()
    top_docs = [documents[i] for i in top_indices]
    top_urls = [links[i] for i in top_indices]

    # Generate answer using OpenAI
    context = "\n\n".join(top_docs)
    prompt = f"Answer the question based on the following context:\n\n{context}\n\nQuestion: {question}"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "links": [
            {"url": top_urls[0], "text": "Related discussion 1"},
            {"url": top_urls[1], "text": "Related discussion 2"}
        ]
    }
