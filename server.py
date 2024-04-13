from fastapi import FastAPI, Body, UploadFile, File
import fitz  # PyMuPDF
from ai import get_ai_response, convert_pdf_to_text
from youtube_transcript_api import YouTubeTranscriptApi
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ImpartEase API", description="API for ImpartEase", version="0.1")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_summary(text):
    """
    Creates a summary of the input text.
    """
    return get_ai_response(
        "Summarize this lecture into 1 page notes in md format, use subheadings and bulleted points and emojis: \n\n"
        + text
    )


def generate_quiz(text):
    """
    Generates a quiz from the input text.
    """
    PROMPT = (
        "Generate a quiz from the following text: \n\n"
        + text
        + "\n\nThe format of the quiz should be multiple choice questions. Return 5 questions as a python list EXACTLY in this format, example: [{'question': 'What is the capital of France?', 'options': ['Paris', 'London', 'Berlin', 'Madrid'], 'answer': 'Paris'}, ...]"
    )
    res = get_ai_response(PROMPT)
    # Parse the response
    try:
        questions = eval(res)
    except SyntaxError:
        return generate_quiz(text)
    return questions


def extract_text_from_pdf(pdf_file):
    """
    Extracts text from a PDF file.
    """
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()

    if not text:
        print("No text found in PDF file")
        pdf_file.seek(0)
        text = convert_pdf_to_text(pdf_file.read())
    return text


def extract_transcript_from_youtube(youtube_link):
    """
    Extracts the transcript from a YouTube video.
    """

    video_id = youtube_link.split("=")[-1]
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    text = ""
    for line in transcript:
        text += line["text"] + " "
    return text


@app.post("/generate/summary/pdf")
async def generate_summary_pdf(pdf_file: UploadFile = File(...)):
    """
    Accepts a PDF file and returns the summary as a text response.
    """
    text = extract_text_from_pdf(pdf_file.file)
    summary = create_summary(text)
    return {"summary": summary}

class YoutubeLink(BaseModel):
    link: str


@app.post("/generate/summary/youtube")
async def generate_summary_youtube(youtube_link: YoutubeLink):
    """
    Accepts a YouTube link and returns the summary as a text response.
    """
    # Extract text from YouTube video

    text = extract_transcript_from_youtube(youtube_link.link)

    summary = create_summary(text)
    # Generate summary
    return {"summary": summary}

class Text(BaseModel):
    text: str

@app.post("/generate/quiz/")
async def generate_quiz_endpoint(text: Text):
    """
    Accepts a PDF file and returns a quiz as a text response.
    """
    quiz = generate_quiz(text.text)
    return {"quiz": quiz}


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
