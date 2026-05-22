from fpdf import FPDF

def make_pdf(filename, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(filename)

make_pdf("mock_resume.pdf", """
Name: Kim Gildong
Email: kim@example.com
Phone: 010-1234-5678

Experience:
- Backend Engineer at Kakao (2022-2024)
  Python, FastAPI, Redis, PostgreSQL
- Junior Developer at Naver (2020-2022)
  Java, Spring Boot

Education:
- Computer Science, Seoul National University (2016-2020)

Skills: Python, FastAPI, LangChain, Redis, Docker, AWS
""")

make_pdf("mock_portfolio.pdf", """
Portfolio

Project 1: AI Interview System
- Built multi-agent interview pipeline using LangGraph
- FastAPI backend, Redis session management
- Tech: Python, FastAPI, LangGraph, Redis

Project 2: Real-time Chat Service
- WebSocket-based chat with 10,000 concurrent users
- Tech: FastAPI, WebSocket, PostgreSQL

GitHub: https://github.com/kimgildong
""")

print("mock_resume.pdf, mock_portfolio.pdf 생성 완료")
