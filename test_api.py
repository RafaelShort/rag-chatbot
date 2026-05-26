import httpx
import json

BASE_URL = "http://localhost:8000"


def print_result(title: str, response: httpx.Response) -> None:
    print(f"\n{'='*50}")
    print(f"TEST: {title}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Body: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception:
        print(f"Body: {response.text}")
    print("="*50)


def test_root():
    r = httpx.get(f"{BASE_URL}/")
    print_result("Root", r)
    assert r.status_code == 200


def test_health():
    r = httpx.get(f"{BASE_URL}/health")
    print_result("Health Check", r)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    print(">>> Health OK")


def test_ingest_text():
    payload = {
        "text": (
            "A Ford foi fundada em 1903 por Henry Ford em Detroit, Michigan. "
            "A empresa revolucionou a industria automotiva com a introducao da "
            "linha de montagem em movimento em 1913, tornando os carros acessiveis "
            "para a populacao em geral. O Modelo T foi o primeiro carro produzido "
            "em massa na historia. Hoje a Ford e uma das maiores montadoras do mundo, "
            "com operacoes em mais de 100 paises. A empresa tem investido fortemente "
            "em veiculos eletricos, com a linha F-150 Lightning e o Mustang Mach-E "
            "como seus principais lancamentos eletricos."
        ),
        "title": "Historia da Ford",
        "metadata": {"source": "test", "language": "pt"}
    }

    r = httpx.post(f"{BASE_URL}/documents/ingest-text", json=payload, timeout=60)
    print_result("Ingest Text", r)
    assert r.status_code == 201
    data = r.json()
    assert "document_id" in data
    assert data["chunks_indexed"] > 0
    print(f">>> Document ID: {data['document_id']}")
    print(f">>> Chunks indexados: {data['chunks_indexed']}")
    return data["document_id"]


def test_collection_info():
    r = httpx.get(f"{BASE_URL}/documents/collection/info")
    print_result("Collection Info", r)
    assert r.status_code == 200


def test_chat(document_id: str):
    payload = {
        "query": "Quando foi fundada a Ford e por quem?",
        "document_id": document_id,
        "top_k": 5,
        "use_reranker": False,
        "stream": False
    }

    # Timeout maior pois Ollama local pode ser mais lento
    r = httpx.post(f"{BASE_URL}/chat", json=payload, timeout=120)
    print_result("Chat RAG", r)
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    print(f">>> Resposta: {data['answer'][:200]}...")
    print(f">>> Fontes encontradas: {data['total_sources_found']}")


def test_delete_document(document_id: str):
    r = httpx.delete(f"{BASE_URL}/documents/{document_id}", timeout=30)
    print_result("Delete Document", r)
    assert r.status_code == 204
    print(">>> Documento deletado com sucesso")


if __name__ == "__main__":
    print("\nIniciando testes end-to-end...\n")

    try:
        test_root()
        print(">>> Root OK")

        test_health()

        test_collection_info()
        print(">>> Collection Info OK")

        document_id = test_ingest_text()

        test_chat(document_id)

        test_delete_document(document_id)

        print("\n" + "="*50)
        print("TODOS OS TESTES PASSARAM!")
        print("="*50)

    except AssertionError as e:
        print(f"\nFALHA: {e}")
    except httpx.ConnectError:
        print("\nERRO: Servidor nao encontrado em http://localhost:8000")
        print("Certifique-se de que o servidor esta rodando.")
    except Exception as e:
        print(f"\nERRO INESPERADO: {type(e).__name__}: {e}")
