# LLM-generated base, adapted by me
from backend.rag import GeminiRAG


def main():
    rag = GeminiRAG()

    question = "Explain what a vector database like LanceDB is used for."
    answer = rag.answer(question)

    print("Q:", question)
    print("A:", answer)


if __name__ == "__main__":
    main()
