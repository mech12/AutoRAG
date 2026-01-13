#!/usr/bin/env python3
"""
커스텀 PDF 데이터를 AutoRAG 평가용 데이터셋으로 변환하는 스크립트

사용법:
    python scripts/prepare_custom_data.py \
        --input_dir docs/sample-data \
        --output_dir data/custom \
        --num_qa 20

환경변수 (.env에서 로드):
    - CUSTOM_LLM_API_BASE: LLM 서버 URL
    - CUSTOM_LLM_MODEL: LLM 모델명
    - CUSTOM_EMBEDDING_API_BASE: 임베딩 서버 URL
    - CUSTOM_EMBEDDING_MODEL: 임베딩 모델명
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_parse_config(output_dir: str) -> str:
    """파싱 설정 YAML 파일 생성"""
    config_content = """modules:
  - module_type: langchain_parse
    file_type: pdf
    parse_method: pdfminer
"""
    config_path = os.path.join(output_dir, "parse_config.yaml")
    os.makedirs(output_dir, exist_ok=True)
    with open(config_path, "w") as f:
        f.write(config_content)
    return config_path


def create_chunk_config(output_dir: str) -> str:
    """청킹 설정 YAML 파일 생성"""
    config_content = """modules:
  - module_type: llama_index_chunk
    chunk_method: Token
    chunk_size: 512
    chunk_overlap: 50
    add_file_name: ko
"""
    config_path = os.path.join(output_dir, "chunk_config.yaml")
    with open(config_path, "w") as f:
        f.write(config_content)
    return config_path


def parse_pdfs(input_dir: str, output_dir: str) -> str:
    """
    PDF 파일들을 파싱
    Returns: 파싱 결과 parquet 파일 경로
    """
    from autorag.parser import Parser

    # Create parse config
    parse_config = create_parse_config(output_dir)

    # Create parser and run
    parse_project_dir = os.path.join(output_dir, "parse_project")
    parser = Parser(
        data_path_glob=os.path.join(input_dir, "**/*.pdf"),
        project_dir=parse_project_dir,
    )
    parser.start_parsing(parse_config)

    # Find the parsed result
    parsed_path = os.path.join(parse_project_dir, "0", "0.parquet")
    if not os.path.exists(parsed_path):
        # Try alternative path
        for root, dirs, files in os.walk(parse_project_dir):
            for f in files:
                if f.endswith(".parquet"):
                    parsed_path = os.path.join(root, f)
                    break

    print(f"Parsed result saved to: {parsed_path}")
    return parsed_path


def chunk_documents(parsed_path: str, output_dir: str) -> str:
    """
    파싱된 문서를 청크로 분할
    Returns: corpus parquet 파일 경로
    """
    from autorag.chunker import Chunker

    # Create chunk config
    chunk_config = create_chunk_config(output_dir)

    # Create chunker and run
    chunk_project_dir = os.path.join(output_dir, "chunk_project")
    chunker = Chunker.from_parquet(
        parsed_data_path=parsed_path,
        project_dir=chunk_project_dir,
    )
    chunker.start_chunking(chunk_config)

    # Find the chunked result
    corpus_path = os.path.join(chunk_project_dir, "0", "0.parquet")
    if not os.path.exists(corpus_path):
        # Try alternative path
        for root, dirs, files in os.walk(chunk_project_dir):
            for f in files:
                if f.endswith(".parquet"):
                    corpus_path = os.path.join(root, f)
                    break

    # Copy to output directory as corpus.parquet
    corpus_df = pd.read_parquet(corpus_path)
    final_corpus_path = os.path.join(output_dir, "corpus.parquet")
    corpus_df.to_parquet(final_corpus_path)

    print(f"Corpus saved to: {final_corpus_path}")
    print(f"Total chunks: {len(corpus_df)}")

    return final_corpus_path, parsed_path


def generate_qa(
    corpus_path: str, parsed_path: str, output_dir: str, num_qa: int = 20
) -> None:
    """
    Corpus에서 QA 데이터셋 생성 (LLM 사용)
    """
    from autorag.data.qa.schema import Raw, Corpus
    from autorag.data.qa.sample import random_single_hop
    from autorag.data.qa.query.llama_gen_query import factoid_query_gen
    from autorag.data.qa.generation_gt.llama_index_gen_gt import make_basic_gen_gt
    from autorag.data.qa.filter.dontknow import dontknow_filter_rule_based
    from llama_index.llms.openai_like import OpenAILike

    # Get LLM settings from environment
    api_base = os.getenv("CUSTOM_LLM_API_BASE")
    model = os.getenv("CUSTOM_LLM_MODEL")
    api_key = os.getenv("CUSTOM_LLM_API_KEY", "dummy")

    if not api_base or not model:
        raise ValueError(
            "CUSTOM_LLM_API_BASE and CUSTOM_LLM_MODEL must be set in .env file"
        )

    print(f"Using LLM: {model} at {api_base}")

    # Create LLM instance
    llm = OpenAILike(
        model=model,
        api_base=api_base,
        api_key=api_key if api_key else "dummy",
        is_chat_model=True,
    )

    # Load data
    raw_df = pd.read_parquet(parsed_path)
    corpus_df = pd.read_parquet(corpus_path)

    raw_instance = Raw(raw_df)
    corpus_instance = Corpus(corpus_df, raw_instance)

    # Generate QA dataset
    qa = (
        corpus_instance.sample(random_single_hop, n=num_qa)
        .map(lambda df: df.reset_index(drop=True))
        .make_retrieval_gt_contents()
        .batch_apply(
            factoid_query_gen,
            llm=llm,
            lang="ko",
        )
        .batch_apply(
            make_basic_gen_gt,
            llm=llm,
            lang="ko",
        )
        .filter(
            dontknow_filter_rule_based,
            lang="ko",
        )
    )

    # Save QA and Corpus
    qa_path = os.path.join(output_dir, "qa.parquet")
    qa.to_parquet(qa_path, corpus_path)

    print(f"Saved QA dataset to {qa_path}")
    print(f"Total QA pairs: {len(qa.data)}")


def generate_qa_simple(
    corpus_path: str, parsed_path: str, output_dir: str, num_qa: int = 20
) -> None:
    """
    간단한 QA 데이터셋 생성 (LLM 없이, 문서 내용 기반)
    """
    import uuid
    from autorag.data.qa.schema import Raw, Corpus
    from autorag.data.qa.sample import random_single_hop

    # Load data
    raw_df = pd.read_parquet(parsed_path)
    corpus_df = pd.read_parquet(corpus_path)

    raw_instance = Raw(raw_df)
    corpus_instance = Corpus(corpus_df, raw_instance)

    # Sample passages
    qa = corpus_instance.sample(random_single_hop, n=num_qa)
    qa = qa.map(lambda df: df.reset_index(drop=True))
    qa = qa.make_retrieval_gt_contents()

    # Create placeholder questions and answers
    qa_df = qa.data.copy()
    qa_df["query"] = qa_df["retrieval_gt_contents"].apply(
        lambda x: f"다음 내용에 대해 설명해주세요: {x[0][0][:100]}..."
        if x and x[0]
        else "내용이 없습니다."
    )
    qa_df["generation_gt"] = qa_df["retrieval_gt_contents"].apply(
        lambda x: [x[0][0][:500]] if x and x[0] else [""]
    )

    # Save
    qa_path = os.path.join(output_dir, "qa.parquet")

    # Ensure required columns exist
    if "qid" not in qa_df.columns:
        qa_df["qid"] = [str(uuid.uuid4()) for _ in range(len(qa_df))]

    save_df = qa_df[["qid", "query", "retrieval_gt", "generation_gt"]].reset_index(
        drop=True
    )
    save_df.to_parquet(qa_path)

    print(f"Saved simple QA dataset to {qa_path}")
    print(f"Total QA pairs: {len(save_df)}")
    print("\n주의: 이 QA는 자동 생성된 플레이스홀더입니다.")
    print("실제 평가를 위해서는 수동으로 질문/답변을 수정하거나 --use_llm 옵션을 사용하세요.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to AutoRAG evaluation dataset"
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing PDF files",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/custom",
        help="Output directory for dataset (default: data/custom)",
    )
    parser.add_argument(
        "--num_qa",
        type=int,
        default=20,
        help="Number of QA pairs to generate (default: 20)",
    )
    parser.add_argument(
        "--use_llm",
        action="store_true",
        help="Use LLM to generate questions and answers (requires .env setup)",
    )
    parser.add_argument(
        "--skip_parse",
        action="store_true",
        help="Skip parsing step (use existing parsed result)",
    )
    parser.add_argument(
        "--skip_qa",
        action="store_true",
        help="Skip QA generation (only parse and chunk)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("AutoRAG 커스텀 데이터 준비")
    print("=" * 60)

    os.makedirs(args.output_dir, exist_ok=True)

    # Step 1: Parse PDFs
    parsed_path = os.path.join(args.output_dir, "parse_project", "0", "0.parquet")
    if args.skip_parse and os.path.exists(parsed_path):
        print(f"\n[1/3] 기존 파싱 결과 사용: {parsed_path}")
    else:
        print("\n[1/3] PDF 파싱 중...")
        parsed_path = parse_pdfs(args.input_dir, args.output_dir)

    # Step 2: Chunk documents
    print("\n[2/3] 문서 청킹 중...")
    corpus_path, parsed_path = chunk_documents(parsed_path, args.output_dir)

    # Step 3: Generate QA
    if not args.skip_qa:
        print("\n[3/3] QA 데이터셋 생성 중...")
        if args.use_llm:
            generate_qa(corpus_path, parsed_path, args.output_dir, args.num_qa)
        else:
            generate_qa_simple(corpus_path, parsed_path, args.output_dir, args.num_qa)

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"\n생성된 파일:")
    print(f"  - {args.output_dir}/corpus.parquet")
    if not args.skip_qa:
        print(f"  - {args.output_dir}/qa.parquet")
    print(f"\n평가 실행:")
    print(f"  make evaluate-custom")


if __name__ == "__main__":
    main()
