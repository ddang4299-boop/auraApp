"""python -m Chatbot.doctor : kiểm tra key + liệt kê model dùng được của từng provider."""
from .llm import _diagnose

if __name__ == "__main__":
    _diagnose()