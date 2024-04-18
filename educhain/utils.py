import pandas as pd
from .models import MCQList  ###

# For creating pdf of the quiz
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# For extracting text from a PDF file
from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS

def to_csv(quiz_data : MCQList, file_name):
    """
    Generate a CSV file from a Quiz object.

    Args:
    quiz_data (Quiz): Instance of the Quiz class containing a list of Question objects.
    file_name (str): Name of the CSV file to be created.
    """
    mcq_data = []

    for question in quiz_data.questions:
        mcq_data.append({
            'question': question.question,
            'option_1': question.options[0],
            'option_2': question.options[1],
            'option_3': question.options[2],
            'option_4': question.options[3],
            'correct_answer': question.correct_answer
        })

    df = pd.DataFrame(mcq_data)
    df.to_csv(file_name, index=False)
    

def to_json(quiz_data : MCQList, file_name=None):

    """
    Convert a list of Question objects to JSON and create a JSON file.

    Args:
    questions (list): List of Question objects.
    file_name (str): Name of the JSON file to be created.
    """
    data = [{"question": question.question, "options": question.options, "correct_answer": question.correct_answer} for question in quiz_data.questions]
    
    df = pd.DataFrame(data)
    
    if file_name:
        df.to_json(file_name, orient='records', indent=4)
        
    return data


def to_pdf(quiz_data : MCQList, file_name, heading=None, subheading=None):
    """
    Create a PDF file from a list of MCQ (Multiple Choice Questions).

    Args:
    questions (list): List of Question objects.
    file_name (str): Name of the PDF file to be created.
    heading (str): Heading for the PDF document. (optional)
    subheading (str): Subheading for the PDF document. (optional)
    """
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(file_name, pagesize=letter)
    elements = []

    if heading:
        elements.append(Paragraph(heading, styles["Heading1"]))

    if subheading:
        elements.append(Paragraph(subheading, styles["Heading2"]))
        elements.append(Spacer(1, 12))

    for i, question in enumerate(quiz_data.questions, start=1):
        question_text = f"{i}. {question.question}"
        elements.append(Paragraph(question_text, styles["BodyText"]))

        for j, option in enumerate(question.options, start=97):
            option_text = f"{chr(j)}) {option}"
            elements.append(Paragraph(option_text, styles["BodyText"]))

        elements.append(Spacer(1, 12))

    elements.append(PageBreak())  # Add a page break before the answers
    elements.append(Paragraph("Answers", styles["Heading1"]))

    for i, question in enumerate(quiz_data.questions, start=1):
        correct_answer_text = f"{i}. {chr(question.options.index(question.correct_answer) + 97)}) {question.correct_answer}"
        elements.append(Paragraph(correct_answer_text, styles["BodyText"]))

    doc.build(elements)

def extract_pdf(file_path):
    """
    Extract text from a PDF file.

    Args:
    file_path (str): Path to the PDF file.

    Returns:
    str: Extracted text from the PDF file.
    """
    
    # provide the path of  pdf file/files.
    pdfreader = PdfReader(file_path)
    
    # read text from pdf
    raw_text = ''
    for i, page in enumerate(pdfreader.pages):
        content = page.extract_text()
        if content:
            raw_text += content
    
    # We need to split the text using Character Text Split such that it sshould not increse token size
    text_splitter = CharacterTextSplitter(
        separator = "\n",
        chunk_size = 1500,
        chunk_overlap  = 200,
        length_function = len,
    )
    texts = text_splitter.split_text(raw_text)
    
    # Download embeddings from OpenAI
    embeddings = OpenAIEmbeddings()
    document_search = FAISS.from_texts(texts, embeddings)
    
    return document_search
    