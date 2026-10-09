# VeLiS-RAG Model Registry

**Current Phase:** Phase 2B (Baseline Hybrid Retrieval)  
**Governance Policy:** Strictly local execution; Tier-A official evidence; zero generative LLM or cross-encoder reranker models permitted.

---

## 1. Registered Embedding Models

### `BAAI/bge-m3`

| Property | Specification / Value |
|---|---|
| **Model Identifier** | `BAAI/bge-m3` |
| **Organization / Author** | Beijing Academy of Artificial Intelligence (BAAI) |
| **Upstream Repository** | [https://huggingface.co/BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) |
| **Exact Commit Revision (SHA)** | `5617a9f61b028005a4858fdac845db406aefb181` |
| **License** | MIT License |
| **Architecture** | XLMRobertaModel (`sentence-transformers` compatible) |
| **Embedding Dimension** | 1024 |
| **Max Sequence Length** | 8192 tokens |
| **Supported Languages** | Multilingual (>100 languages, verified on English and Hindi Devanagari script) |
| **Primary Task in Pipeline** | Dense semantic embedding of Tier-A normalized passage chunks and user queries |
| **Registration / Download Date** | 2026-10-10 |
| **Designated Local Storage** | `data/models/bge-m3` |
| **Execution Environment** | Local CPU / CUDA (purely offline after download, zero network calls during inference) |

---

## 2. File Manifest & Key Verification Hashes

The upstream snapshot commit `5617a9f61b028005a4858fdac845db406aefb181` contains the following core component files:

| Filename | Purpose | Type | Verified SHA-256 Checksum |
|---|---|---|---|
| `config.json` | XLM-RoBERTa architecture parameters | JSON configuration | `26159e7ad065073448460117eb24b7a4572f6f4e78eadff65dc0a11c052449fa` |
| `tokenizer_config.json` | Tokenizer special tokens and settings | JSON configuration | `a62b2b6784f990259fddef5f16388693a8043be4f69179e6a5257eeb3f9abac4` |
| `modules.json` | Transformer + Pooling module order | JSON configuration | `84e40c8e006c9b1d6c122e02cba9b02458120b5fb0c87b746c41e0207cf642cf` |
| `sentencepiece.bpe.model` | Byte-Pair Encoding sentencepiece vocabulary | Binary tokenizer model | `cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865` |
| `tokenizer.json` | Fast tokenization definition | JSON tokenizer | `21106b6d7dab2952c1d496fb21d5dc9db75c28ed361a05f5020bbba27810dd08` |
| `pytorch_model.bin` | Model weights (dense encoder) | Model weights (2.27 GB) | `b5e0ce3470abf5ef3831aa1bd5553b486803e83251590ab7ff35a117cf6aad38` |
| `1_Pooling/config.json` | Mean pooling configuration | JSON configuration | Verified |

---

## 3. Governance Boundaries & Prohibitions

1. **Embedding-Only Authorization**:
   - `BAAI/bge-m3` is authorized exclusively for dense vector representation in the Phase 2B hybrid retrieval baseline.
2. **Generative LLM Prohibition**:
   - No language generation model (e.g. Llama, Mistral, Gemma, Qwen, GPT) is permitted in Phase 2B. Answer generation is out of scope.
3. **Cross-Encoder Reranker Prohibition**:
   - No neural reranker or cross-encoder model (e.g., `bge-reranker-large`) is permitted in Phase 2B. Hybrid fusion is strictly achieved via deterministic Reciprocal Rank Fusion (RRF with $k=60$).
4. **Network & Cloud Isolation**:
   - Once downloaded and verified, model execution must be strictly offline (`local_files_only=True`). No telemetry, external inference APIs, or remote endpoint requests are permitted.
5. **Prompt Injection Mitigation**:
   - Retrieved chunks and embeddings are strictly treated as data payloads for similarity measurement, never executed or evaluated as instructions.

---

## 4. Local Installation and Reproducibility Instructions

To reproduce the local download and verify the model artifact:

```bash
# Set local directory
python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id='BAAI/bge-m3',
    revision='5617a9f61b028005a4858fdac845db406aefb181',
    local_dir='data/models/bge-m3',
    local_dir_use_symlinks=False
)
"
```

To load in Python for embedding inference:

```python
from sentence_transformers import SentenceTransformer

# Load strictly from local storage with local_files_only
model = SentenceTransformer("data/models/bge-m3", local_files_only=True)
embeddings = model.encode(["Example text in English", "सूचना का अधिकार अधिनियम 2005"])
assert embeddings.shape[1] == 1024
```
